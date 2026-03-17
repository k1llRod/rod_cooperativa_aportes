from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


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
    loan_count = fields.Integer(string='Préstamos', compute='compute_contributions_count', store=True)
    loan_count_mortgage = fields.Integer(string='Préstamos', compute='compute_contributions_count')
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

    since = fields.Date(string='Desde', related='partner_payroll_ids.since_payment', store=True)
    until = fields.Date(string='Hasta', related='partner_payroll_ids.until_payment', store=True)

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