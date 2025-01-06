from odoo import api, fields, models, _

class ReportCategoryB(models.AbstractModel):
    _name = 'report.rod_cooperativa_aportes.report_category_b'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        partner_payroll = self.env['partner.payroll'].search([('partner_status_especific', '=', 'passive_reserve_b'), ('state', '=', 'process')], order='partner_id')
        sheet = workbook.add_worksheet('Aportes')

        a = 0
        b = 1
        c = 2
        d = 3
        e = 4
        f = 5
        g = 6
        h = 7
        i = 8
        j = 9
        trow = 0
        row = 8
        col = 0
        n = 0
        border_format_header = workbook.add_format({
            'border': 1,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })
        border_format = workbook.add_format({
            'border': 1
        })
        title_header_page = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 8,
            # 'bg_color': '#F7F7F7'
        })

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,
            # 'bg_color': '#F7F7F7'
        })

        # Define a format for the cells with borders
        cell_format = workbook.add_format({
            'border': 1
        })

        sheet.merge_range('A1:B1', 'COOPERATIVA DE AHORRO Y CREDITO DE VINCULO LABORAL', title_header_page)
        sheet.merge_range('A2:B2', '"COA - 4 DE DICIEMBRE" R.L.', title_header_page)
        sheet.merge_range('A3:B3', 'BOLIVIA', title_header_page)
        # sheet.write(0, a, 'COOPERATIVA DE AHORRO Y CREDITO DE VINCULO LABORAL', title_format)
        # sheet.write(1, a, '"COA - 4 DE DICIEMBRE" R.L.')
        # sheet.write(2, a, 'BOLIVIA')
        sheet.merge_range('A4:D4', 'RELACION NOMINAL DEL PERSONAL DE OFICIALES DEL SERVICIO PASIVO ASOCIADOS CATEGORIA "B" QUE SE', title_format)
        sheet.merge_range('A5:D5','ENCUENTRAN AFILIADOS EN LA COOPERATIVA DE AHORRO Y CREDITO DE VINCULO LABORAL "COA 4 - DE DICIEMBRE" R.L.', title_format)
        sheet.write(row, a, 'N', border_format)
        sheet.write(row, b, 'SOCIO', border_format)
        # sheet.write(row, c, 'Ciudad', border_format)
        sheet.write(row, c, '2023', border_format)
        sheet.write(row, d, '2024', border_format)
        sheet.write(row, e, '2025', border_format)
        sheet.write(row, f, 'OBSERVACIONES', border_format)

        for partner in partner_payroll:
            partner.compute_updated_partner()
            n += 1
            row += 1
            sheet.write(row, a, n,border_format)
            sheet.write(row, b, partner.partner_id.name,border_format)
            # sheet.write(row, c, partner.city,border_format)
            z = c
            y = c
            srow = 0
            for due in partner.due_payments_ids:
                # sheet.write(row, z, due.gestion)
                sheet.write(row, y, round(due.d_total,2),border_format) if due.d_total > 0 else sheet.write(row, y, 0,border_format)
                z += 1
                y += 1
