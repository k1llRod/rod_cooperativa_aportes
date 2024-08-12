from odoo import models, fields, api, _

class WizardPayrollReturn(models.TransientModel):
    _name = 'wizard.payroll.return'

    name = fields.Char(string='ID aporte')
    date_pivote = fields.Date(string='Fecha pivote', default=fields.Datetime.now())
    period = fields.Char(string='Periodo', compute="compute_period_register")
    payment_date = fields.Date(string='Fecha de pago', default=fields.Datetime.now())
    mount = fields.Float(string='Monto', required=True)
    glosa = fields.Text(string='Glosa')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Planilla aporte')

    @api.depends('date_pivote')
    def compute_period_register(self):
        for record in self:
            record.period = record.date_pivote.strftime('%m-%Y')


    def action_confirm(self):
        a = 1
        payroll_payments = self.env['payroll.payments'].create({
            'date_pivote': self.date_pivote,
            'payment_date': self.payment_date,
            'income': (self.mount)*-1 if self.mount > 0 else self.mount,
            'income_passive': 0,
            'regulation_cup': 0,
            'miscellaneous_income': 0,
            'state': 'partner_return',
            'partner_payroll_id': self.partner_payroll_id.id,
            'glosa_contribution_interest': self.glosa
        })
        b = 1


