from odoo import api, fields, models, _

class ReportReportForm(models.AbstractModel):
    _name = 'report.rod_cooperativa_aportes.report_form_loan'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        partner_payroll = self.env['partner.payroll'].search([('partner_status_especific', '=', data['partner_status_especific'])])
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
        row = 0
        col = 0
        n = 0
        if data['partner_status_especific'] == 'passive_reserve_b':
            sheet.write(row, a, 'N')
            sheet.write(row, b, 'Socio')
            sheet.write(row, c, 'Gestion')
            sheet.write(row, d, 'D.Inscripcion')
            sheet.write(row, e, 'D.Tasa de regulacion')
            sheet.write(row, f, 'D.Aporte obligatorio')
            sheet.write(row, g, 'D.Aporte voluntario')
            sheet.write(row, h, 'D.Post mortem')
            sheet.write(row, i, 'Total debe')
            for partner in partner_payroll:
                partner.compute_updated_partner()
                n += 1
                row += 1
                sheet.write(row, a, n)
                sheet.write(row, b, partner.partner_id.name)
                srow = 0
                for due in partner.due_payments_ids:
                    row += 1
                    sheet.write(row, c, due.gestion)
                    sheet.write(row, d, round(due.d_miscellaneous_income,2))
                    sheet.write(row, e, round(due.d_regulation_cup,2))
                    sheet.write(row, f, round(due.d_mandatory_contribution,2))
                    sheet.write(row, g, round(due.d_voluntary_contribution,2))
                    sheet.write(row, h, round(due.d_post_mortem,2))
                    sheet.write(row, i, round(due.d_total,2))

        if data['partner_status_especific'] == 'passive_reserve_a':
            sheet.write(row, a, 'N')
            sheet.write(row, b, 'Socio')
            sheet.write(row, c, 'Gestion')
            sheet.write(row, d, 'D.Inscripcion')
            sheet.write(row, e, 'D.Tasa de regulacion')
            sheet.write(row, f, 'D.Aporte obligatorio')
            sheet.write(row, g, 'D.Aporte voluntario')
            sheet.write(row, h, 'D.Post mortem')
            sheet.write(row, i, 'Total debe')
            for partner in partner_payroll:
                partner.compute_updated_partner()
                n += 1
                row += 1
                sheet.write(row, a, n)
                sheet.write(row, b, partner.partner_id.name)
                srow = 0
                for due in partner.due_payments_ids:
                    row += 1
                    sheet.write(row, c, due.gestion)
                    sheet.write(row, d, round(due.d_miscellaneous_income,2))
                    sheet.write(row, e, round(due.d_regulation_cup,2))
                    sheet.write(row, f, round(due.d_mandatory_contribution,2))
                    sheet.write(row, g, round(due.d_voluntary_contribution,2))
                    sheet.write(row, h, round(due.d_post_mortem,2))
                    sheet.write(row, i, round(due.d_total,2))

