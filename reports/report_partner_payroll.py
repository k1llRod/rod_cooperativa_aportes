from odoo import api, fields, models, _

class PartnerPayrollReport(models.AbstractModel):
    _name = 'report.rod_cooperativa_aportes.partner_payroll_report'

    # @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('rod_cooperativa_aportes.report_partner_payroll')

        # your report data structure goes in data_array
        data_array = []
        docargs = {
            'hold_data_array': data_array,
        }
        # here we will pass the report data into our report template
        return report_obj.render('rod_cooperativa_aportes.report_my_custom_report', docargs)
