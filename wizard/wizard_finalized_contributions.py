from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class WizardFinalizedContributions(models.TransientModel):
    _name = 'wizard.finalized.contributions'
    _description = 'Form Finalized Contributions'

    name = fields.Char(string = 'name')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Codigo Aporte')
    loan_application_id = fields.Many2one('loan.application', string='Codigo Prestamo')
    partner_name = fields.Char(string='Nombre del asociado', related="loan_application_id.partner_id.name")
    date_finalize = fields.Date(string='Fecha de Finalizacion', required=True)
    disengagement = fields.Float(string='Desvinculacion', required=True, default=10)
    total_mandatory_contributions_certificate = fields.Float(string='Total de aportes obligatorios', required=True)
    total_voluntary_contributions_certificate = fields.Float(string='Total de aportes voluntarios', required=True)
    capital_initial = fields.Float('Total capital inicial')
    total_other_contributions = fields.Float(string='Total de otros aportes', required=True)
    total_performance_contributions = fields.Float(string='Total rendimiento de aportes', required=True)
    total_contributions = fields.Float(string='Total aportes')
    total_loan_capital = fields.Float(string='Total saldo de prestamo $.', required=True)
    total_balance_total_interest_month = fields.Float(string='Total saldo interes mensual', required=True)
    default_dolar = fields.Float(string='Dolar $')
    total_loan_capital_bolivianos = fields.Float(string='Total saldo prestamo Bs.')
    total_balance_total_interest_month_bolivianos = fields.Float(string='Total saldo interes mensual Bs.')

    def action_confirm(self):
        if self.total_loan_capital >= 0:
            raise UserError(_('Tiene un prestamo vigente, dar de baja el prestamo.'))

        name = self.env['ir.sequence'].next_by_code('finalize.contributions')
        vals = {
            'name': name,
            'partner_payroll_id': self.partner_payroll_id.id,
            'date_finalize': self.date_finalize,
            'disengagement': self.disengagement,
            'total_mandatory_contributions_certificate': self.total_mandatory_contributions_certificate,
            'total_voluntary_contributions_certificate': self.total_voluntary_contributions_certificate,
            'total_other_contributions': self.total_other_contributions,
            'total_performance_contributions': self.total_performance_contributions,
            'total_loan_capital': self.total_loan_capital,
            'total_loan_capital_bolivianos': self.total_loan_capital_bolivianos,
            'total_balance_total_interest_month': self.total_balance_total_interest_month,
            'total_balance_total_interest_month_bolivianos': self.total_balance_total_interest_month_bolivianos,
        }
        record = self.partner_payroll_id.finalize_contributions_id.create(vals)
        if record:
            self.partner_payroll_id.state = 'process_finalized'
            self.partner_payroll_id
        else:
            raise ValidationError('Error al generar la liquidacion del asociado')