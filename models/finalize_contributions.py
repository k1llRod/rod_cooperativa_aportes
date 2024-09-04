from odoo import models, fields, api, _

class FinalizeContributions(models.Model):
    _name = 'finalize.contributions'
    _description = 'Finalize Contributions'

    name = fields.Char(string='Codigo', required=True)
    partner_payroll_id = fields.Many2one('partner.payroll', string='Codigo Aporte')
    date_finalize = fields.Date(string='Fecha de Finalizacion')
    disengagement = fields.Float(string='Desvinculacion', required=True, default=10)
    total_mandatory_contributions_certificate = fields.Float(string='Total de aportes obligatorios', required=True)
    total_voluntary_contributions_certificate = fields.Float(string='Total de aportes voluntarios', required=True)
    total_other_contributions = fields.Float(string='Total de otros aportes', required=True)
    total_performance_contributions = fields.Float(string='Total rendimiento de aportes', required=True)
    total_loan_capital = fields.Float(string='Total saldo de prestamo $', required=True)
    total_balance_total_interest_month = fields.Float(string='Total saldo interes mensual', required=True)
    default_dolar = fields.Float(string='Dolar $')
    total_loan_capital_bolivianos = fields.Float(string='Total saldo prestamo Bs.')
    total_balance_total_interest_month_bolivianos = fields.Float(string='Total saldo interes mensual Bs.')



    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Realizado'),
    ], string='Estado', default='draft')



    def finalize_contributions(self):
        # Here you can write the code to finalize the contributions
        return True