from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import base64
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from odoo.exceptions import UserError
from odoo.modules import get_module_resource


class ResPartner(models.Model):
    _inherit = 'res.partner'

    state = fields.Selection([('draft', 'Borrador'),
                              ('verificate', 'Verificación'),
                              ('activate', 'Socio activo'),
                              ('external','Externo'),
                              ('rejected', 'Rechazado'),
                              ('unsubscribe', 'Baja'),
                              ('deceased','Fallecido'),
                              ('unassociated','No asociado'),
                              ('expelled','Expulsion'),
                              ('abandonment','Abandono')],
                             string='Estado', default='draft', track_visibility='onchange')
    # date_deceased = fields.Date(string='Fecha de fallecimiento')

    def init_partner(self):
        partner_payroll = self.env['partner.payroll'].create({'partner_id': self.id,
                                                              'date_registration': datetime.now(),
                                                              # 'total_contribution': 0,
                                                              # 'advanced_payments': 0,
                                                              })
        view_id = self.env.ref('rod_cooperativa_aportes.action_partner_payroll')
        return {
            'name': 'Detalle del Registro',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.payroll',
            'res_id': partner_payroll.id,
            'view_mode': 'form',
            'target': 'current',
        }

    contributions_count = fields.Integer(string='Aportes', compute='compute_contributions_count', store=True)
    loan_count = fields.Integer(string='Préstamos regulares', compute='compute_contributions_count', store=True)
    loan_count_mortgage = fields.Integer(string='Préstamos hipotecarios', compute='compute_contributions_count', store=True)
    loan_count_loan_emergency = fields.Integer(string='Préstamos', compute='compute_contributions_count')
    date_unsubscribe = fields.Date(string='Fecha de baja')

    partner_payroll_ids = fields.Many2one('partner.payroll', string='Aportes', compute='compute_contributions_count', store=True)
    loan_application_ids = fields.Many2one('loan.application', string='Préstamos', compute='compute_contributions_count', store=True)

    type_disengagements = fields.Selection([('fallecimiento', 'Fallecimiento'),
                                            ('retiro_voluntario', 'Retiro voluntario'),
                                            ('pase_servicio_pasivo', 'Pase al servicio pasivo'),
                                            ('abandono', 'Abandono'),
                                            ('expulsion', 'Expulsion')],
                                           string="Baja por", related='partner_payroll_ids.type_disengagements', store=True)
    date_disengagements = fields.Date(string='Fecha de baja', related='partner_payroll_ids.date_disengagements', store=True)
    gloss_disengagement = fields.Text(string='Glosa de baja', related='partner_payroll_ids.gloss_disengagement', store=True)

    since = fields.Date(string='Fecha de pase al sevicio pasivo', related='partner_payroll_ids.since_payment', store=True)
    until = fields.Date(string='Hasta', related='partner_payroll_ids.until_payment', store=True)
    date_burn_partner = fields.Datetime(string='Fecha de filiacion', related='partner_payroll_ids.date_burn_partner', store=True)

    def compute_contributions_count(self):
        for record in self:
            # 1. Usar search_count (Solo cuenta en BD, no trae datos)
            record.contributions_count = self.env['partner.payroll'].search_count([('partner_id', '=', record.id)])

            # Filtros optimizados para conteos
            record.loan_count = self.env['loan.application'].search_count([
                ('partner_id', '=', record.id),
                ('with_guarantor', '!=', 'mortgage'),
                ('state', '=', 'progress')
            ])
            record.loan_count_mortgage = self.env['loan.application'].search_count([
                ('partner_id', '=', record.id),
                ('with_guarantor', '=', 'mortgage'),
                ('state', '=', 'progress')
            ])
            record.loan_count_loan_emergency = self.env['loan.application.emergency'].search_count([
                ('partner_id', '=', record.id)
            ])

            # 2. Obtener el último registro eficientemente (Sin cargar toda la lista)
            # Asumiendo que quieres el último creado (order='id desc')
            if record.contributions_count > 0:
                record.partner_payroll_ids = self.env['partner.payroll'].search(
                    [('partner_id', '=', record.id)],
                    order='id desc',
                    limit=1
                )
            else:
                record.partner_payroll_ids = False

            if record.loan_count > 0:
                record.loan_application_ids = self.env['loan.application'].search(
                    [('partner_id', '=', record.id)],
                    order='id desc',
                    limit=1
                )
            else:
                record.loan_application_ids = False
    def action_view_contributions(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa_aportes.action_partner_payroll")
        action['domain'] = [
            ('partner_id.id', '=', self.id),
        ]
        return action

    def action_view_loans(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa.action_loan_application")
        action['domain'] = [
            ('partner_id.id', '=', self.id),
            ('with_guarantor','!=','mortgage')
        ]
        return action
    def action_view_loans_mortgage(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa.action_loan_application")
        action['domain'] = [
            ('partner_id.id', '=', self.id),
            ('with_guarantor','=','mortgage')
        ]
        return action
    def action_view_loans_emergency(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa.action_loan_emergency_application")
        action['domain'] = [
            ('partner_id.id', '=', self.id)
        ]
        return action

    def approve_verification(self):
        self.ensure_one()
        if self.state == 'draft':
            if not self.code_contact:
                raise ValidationError(_('Debe ingresar el código de contacto'))
            if not self.partner_status_especific:
                raise ValidationError(_('Debe ingresar la situación del socio'))
            if not self.ci_photocopy:
                raise ValidationError(_('Debe ingresar la Fotocopía de la cédula de identidad'))
            if not self.photocopy_military_ci:
                raise ValidationError(_('Debe ingresar la Fotocopia de la  cédula militar'))
            if self.partner_status == 'external':
                self.state = 'external'
            else:
                self.state = 'verificate'

    def approve_partner(self):
        self.ensure_one()
        if self.state == 'verificate':
            self.state = 'activate'

    def return_form(self):
        self.ensure_one()
        if self.state == 'verificate':
            self.state = 'draft'

    def init_loan(self):
        loan_application = self.env['loan.application'].create({'partner_id': self.id,
                                                                'date_application': datetime.now(),
                                                                'type_loan': 'regular',
                                                                })
        return {
            'name': 'Detalle del prestamo',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.application',
            'res_id': loan_application.id,
            'view_mode': 'form',
            'target': 'current',
        }
    def init_loan_mortgage(self):
        loan_application = self.env['loan.application'].create({'partner_id': self.id,
                                                                'date_application': datetime.now(),
                                                                'type_loan': 'regular',
                                                                'with_guarantor': 'mortgage',
                                                                })
        return {
            'name': 'Detalle del prestamo',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.application',
            'res_id': loan_application.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def init_loan_emergency(self):
        loan_application = self.env['loan.application.emergency'].create({'partner_id': self.id,
                                                                         'date': datetime.now(),
                                                                         })
        return {
            'name': 'Detalle del prestamo',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.application.emergency',
            'res_id': loan_application.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def init_massive_payment(self):
        partners_off = self.env['partner.payroll'].search([])
        domain = []
        for partner in partners_off:
            domain.append(partner.partner_id.id)
        partners_init = self.filtered(lambda x:x.id not in domain)
        for rec in partners_init:
            rec.init_partner()

    def form_unsubscribe(self):
        a = 1
        context = {
            'default_partner_id': self.id,
        }
        return {
            'name': 'Baja de socio',
            'type': 'ir.actions.act_window',
            'res_model': 'form.deseaced',
            'partner_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
    def unsubscribe(self):
        self.ensure_one()
        verificate_contribution = self.env['partner.payroll'].search([('partner_id','=',self.id)])
        if verificate_contribution.state != 'finalized':
            raise ValidationError(_('No se puede dar de baja a un socio que tiene aportes registrados'))
        self.date_unsubscribe = datetime.now()
        self.state = 'unsubscribe'

    def print_report_partner_elections(self):
        return self.env.ref('rod_cooperativa_aportes.report_res_partner_elections').report_action(self)

    def registry_payment_post_mortem(self):
        family_ids = self.family_id.filtered(lambda x:x.beneficiary == True).ids
        context = {
            'default_partner_id': self.id,
            'default_family_ids': family_ids,
            'default_global_amount': self.global_amount,
            'default_base_amount':self.base_amount,
            'default_base_longevity_amount': self.base_longevity,
        }
        return {
            'name': 'Pago post mortem',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.post.mortem',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }

    def verification_massive(self):
        for rec in self:
            rec.state = 'verificate'

    def draft_massive(self):
        for rec in self:
            rec.state = 'draft'

    def print_report_unsubscribe(self):
        return self.env.ref('rod_cooperativa_aportes.action_partner_unsubscribe_pdf').report_action(self)

    def action_generate_birthday_card(self):
        self.ensure_one()

        # 1. Obtener la ruta de la plantilla limpia
        image_base_path = get_module_resource(
            'rod_cooperativa_aportes',
            'static', 'src', 'img', 'template_cumpleanos.png'
        )

        if not image_base_path:
            raise UserError("No se encontró la plantilla en: static/src/img/template_cumpleanos.png")

        # 2. Configuración de fuentes (Cursiva ordinaria y Cursiva+Negrita para el nombre)
        try:
            font_path_italic = "C:\\Windows\\Fonts\\timesi.ttf"  # Cursiva estándar (Italic)
            font_path_bold_italic = "C:\\Windows\\Fonts\\timesbi.ttf"  # Negrita + Cursiva (Bold Italic)

            font_body = ImageFont.truetype(font_path_italic, 32)
            font_name = ImageFont.truetype(font_path_bold_italic, 32)  # Mismo tamaño para no desalinear el renglón
        except IOError:
            font_body = ImageFont.load_default()
            font_name = ImageFont.load_default()

        try:
            img = Image.open(image_base_path)
            draw = ImageDraw.Draw(img)
        except Exception as e:
            raise UserError(f"Error al abrir la plantilla base: {str(e)}")

        # 3. Datos dinámicos del asociado (Normalizamos espacios)
        grado = self.category_partner_id[0].code_loan if self.category_partner_id else ''
        nombre_completo = self.name or ''
        texto_socio_completo = f"{grado} {nombre_completo}"
        texto_socio_completo = " ".join(texto_socio_completo.split()).strip()

        # 4. Textos oficiales consolidados
        bloque_unificado = (
            f"A nombre de los miembros del Directorio y el Consejo de Administración, "
            f"Socios y mío en particular, saludo muy atentamente al {texto_socio_completo}, "
            f"a objeto de expresarle las más sinceras felicitaciones en ocasión de conmemorar su "
            f"“ANIVERSARIO NATAL”, acontecimiento de suma importancia, manifestándole su trayectoria, "
            f"liderazgo impecable y entrega incondicional a nuestro Ejército y las FF.AA., "
            f"es un vivo ejemplo para las nuevas generaciones y nuestra Institución."
        )

        bloque_deseos = (
            "Le deseo el mayor de los éxitos, en sus actividades y que este nuevo año "
            "de vida este lleno de bendiciones junto a su distinguida familia."
        )

        bloque_cierre = "Con este especial motivo, saludo a Ud. con las consideraciones más distinguidas."

        color_texto = (26, 26, 26)
        ancho_imagen, alto_imagen = img.size

        # 5. Configuración de márgenes, espaciados y sangría
        margin_left = 225
        max_text_width = ancho_imagen - (margin_left * 2)
        current_y = 430
        line_spacing = 40
        paragraph_spacing = 50
        indent_pixels = 60

        # Algoritmo de renderizado posicional preciso (Maneja Sangrías y cambia a Bold Italic en el rango del nombre)
        def draw_justified_paragraph_with_bold_italic(text, target_bold_text, font_regular, font_bold_italic, y_start,
                                                      indent=60):
            # Encontramos la posición exacta en caracteres de dónde empieza y termina el nombre
            start_bold_idx = text.find(target_bold_text)
            end_bold_idx = start_bold_idx + len(target_bold_text) if start_bold_idx != -1 else -1

            words = text.split()
            first_line_words = []
            current_w = indent

            # Reconstrucción de la primera línea con índices dinámicos
            char_counter = 0
            while words:
                word = words[0]
                word_start_in_text = text.find(word, char_counter)

                is_bold = False
                if start_bold_idx != -1 and word_start_in_text >= start_bold_idx and word_start_in_text < end_bold_idx:
                    is_bold = True

                f_actual = font_bold_italic if is_bold else font_regular
                bbox = draw.textbbox((0, 0), word, font=f_actual)
                word_w = bbox[2] - bbox[0]
                space_w = draw.textbbox((0, 0), " ", font=f_actual)[2] - draw.textbbox((0, 0), " ", font=f_actual)[0]

                if current_w + word_w > max_text_width:
                    break

                char_counter = word_start_in_text + len(word)
                first_line_words.append(words.pop(0))
                current_w += word_w + space_w

            remaining_text = " ".join(words)
            lines = textwrap.wrap(remaining_text, width=46)
            lines.insert(0, " ".join(first_line_words))
            y = y_start

            global_char_idx = 0

            for i, line in enumerate(lines):
                line_words = line.split()
                if not line_words:
                    continue

                current_margin_left = margin_left + indent if i == 0 else margin_left
                current_max_width = max_text_width - indent if i == 0 else max_text_width

                # Regla de fin de párrafo (Alineado normal a la izquierda)
                if i == len(lines) - 1:
                    x_cursor = current_margin_left
                    for word in line_words:
                        global_char_idx = text.find(word, global_char_idx)
                        is_bold = (
                                    start_bold_idx != -1 and global_char_idx >= start_bold_idx and global_char_idx < end_bold_idx)

                        f_actual = font_bold_italic if is_bold else font_regular
                        draw.text((x_cursor, y), word, fill=color_texto, font=f_actual)

                        word_w = draw.textbbox((0, 0), word, font=f_actual)[2] - \
                                 draw.textbbox((0, 0), word, font=f_actual)[0]
                        space_w = draw.textbbox((0, 0), " ", font=f_actual)[2] - \
                                  draw.textbbox((0, 0), " ", font=f_actual)[0]
                        x_cursor += word_w + space_w
                        global_char_idx += len(word)
                    y += line_spacing
                    continue

                # Calcular el tamaño de las palabras respetando si es Regular o Bold Italic
                words_width = 0
                temp_char_idx = global_char_idx
                for word in line_words:
                    temp_char_idx = text.find(word, temp_char_idx)
                    is_bold = (
                                start_bold_idx != -1 and temp_char_idx >= start_bold_idx and temp_char_idx < end_bold_idx)
                    f_actual = font_bold_italic if is_bold else font_regular
                    bbox = draw.textbbox((0, 0), word, font=f_actual)
                    words_width += (bbox[2] - bbox[0])
                    temp_char_idx += len(word)

                total_space_width = current_max_width - words_width
                num_spaces = len(line_words) - 1
                space_width = total_space_width / num_spaces if num_spaces > 0 else 0

                # Renderizado palabra por palabra aplicando el estilo exacto
                x_cursor = current_margin_left
                for word in line_words:
                    global_char_idx = text.find(word, global_char_idx)
                    is_bold = (
                                start_bold_idx != -1 and global_char_idx >= start_bold_idx and global_char_idx < end_bold_idx)

                    f_actual = font_bold_italic if is_bold else font_regular
                    draw.text((x_cursor, y), word, fill=color_texto, font=f_actual)

                    word_w = draw.textbbox((0, 0), word, font=f_actual)[2] - draw.textbbox((0, 0), word, font=f_actual)[
                        0]
                    x_cursor += word_w + space_width
                    global_char_idx += len(word)

                y += line_spacing
            return y

        # --- GENERACIÓN DE CAPAS ---
        # Pasamos como objetivo 'texto_socio_completo' para aplicar estrictamente Bold Italic en todo el bloque del nombre
        current_y = draw_justified_paragraph_with_bold_italic(bloque_unificado, texto_socio_completo, font_body,
                                                              font_name, current_y, indent=indent_pixels)
        current_y += paragraph_spacing

        current_y = draw_justified_paragraph_with_bold_italic(bloque_deseos, "", font_body, font_name, current_y,
                                                              indent=indent_pixels)
        current_y += paragraph_spacing

        current_y = draw_justified_paragraph_with_bold_italic(bloque_cierre, "", font_body, font_name, current_y,
                                                              indent=indent_pixels)

        # 6. Procesamiento final de la imagen
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        img_str = base64.b64encode(buffer.getvalue())
        buffer.close()

        # 7. Crear el adjunto y enviarlo al navegador
        attachment = self.env['ir.attachment'].create({
            'name': f"Felicitacion_{self.name.replace(' ', '_')}.jpg",
            'type': 'binary',
            'datas': img_str,
            'mimetype': 'image/jpeg',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }