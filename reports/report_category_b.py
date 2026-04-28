from odoo import api, fields, models, _

class ReportCategoryB(models.AbstractModel):
    _name = 'report.rod_cooperativa_aportes.report_category_b'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard_record):
        # 1. Recuperar años del wizard
        gestiones_objetivo = data.get('years', [])

        # 2. Obtener registros de socios
        # Nota: Aquí filtramos según lo que definiste originalmente
        partner_payroll = self.env['partner.payroll'].search([
            ('partner_status_especific', '=', 'passive_reserve_b'),
            ('state', '=', 'process')
        ], order='partner_id')

        sheet = workbook.add_worksheet('Aportes')

        # 3. Definición de Formatos
        title_style = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 12})
        header_style = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#E9E9E9'})
        text_style = workbook.add_format({'border': 1, 'align': 'left'})
        num_style = workbook.add_format({'border': 1, 'align': 'right', 'num_format': '#,##0.00'})
        int_style = workbook.add_format({'border': 1, 'align': 'center'})

        # 4. Encabezados de la Empresa
        sheet.merge_range('A1:C1', 'COOPERATIVA DE AHORRO Y CREDITO DE VINCULO LABORAL', title_style)
        sheet.merge_range('A2:C2', '"COA - 4 DE DICIEMBRE" R.L.', title_style)
        sheet.merge_range('A4:F4', 'RELACION NOMINAL DEL PERSONAL DE OFICIALES DEL SERVICIO PASIVO', title_style)

        # 5. Cabeceras de Tabla Dinámicas
        row = 8
        sheet.write(row, 0, 'N°', header_style)
        sheet.write(row, 1, 'SOCIO', header_style)

        col_ptr = 2
        for gestion in gestiones_objetivo:
            sheet.write(row, col_ptr, gestion, header_style)
            col_ptr += 1

        sheet.write(row, col_ptr, 'OBSERVACIONES', header_style)

        # 6. Llenado de Datos
        row += 1
        counter = 1

        for partner in partner_payroll:
            # Actualizar datos del socio antes de escribir
            partner.compute_updated_partner()

            sheet.write(row, 0, counter, int_style)
            sheet.write(row, 1, partner.partner_id.name or '', text_style)

            # Mapeo de aportes por año { '2023': 150.00 }
            pagos_dict = {str(due.gestion): due.d_total for due in partner.due_payments_ids}

            current_col = 2
            for gestion in gestiones_objetivo:
                monto = pagos_dict.get(gestion, 0.0)
                # Escribir solo si es mayor a 0, de lo contrario 0
                sheet.write(row, current_col, monto if monto > 0 else 0.0, num_style)
                current_col += 1

            # Celda de observaciones vacía con borde
            sheet.write(row, current_col, '', text_style)

            row += 1
            counter += 1

        # Ajustar ancho de columnas automáticamente (opcional)
        sheet.set_column('B:B', 40)  # Nombre del socio más ancho
