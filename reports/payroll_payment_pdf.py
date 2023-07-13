from odoo import models

class reportPaymentPayroll(models.AbstractModel):
    _name = 'report.payment.payroll'
    def _get_report_values(self, docids, data=None):
        docs = self.env['payroll.payments'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'payroll.payments',
            'docs': docs,
        }