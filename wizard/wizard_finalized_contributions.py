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
    disengagement = fields.Float(string='Desvinculacion', default=10)
    total_mandatory_contributions_certificate = fields.Float(string='Total de aportes obligatorios', required=True)
    total_voluntary_contributions_certificate = fields.Float(string='Total de aportes voluntarios', required=True)
    capital_initial = fields.Float('Total capital inicial')
    total_other_contributions = fields.Float(string='Total otros aportes', required=True)
    total_surpluses = fields.Float(string='Total excedentes', required=True)
    total_performance_contributions = fields.Float(string='Total rendimiento de aportes', required=True)
    total_contributions = fields.Float(string='Total aportes')
    total_loan_capital = fields.Float(string='Total saldo de prestamo $.', required=True)
    total_balance_total_interest_month = fields.Float(string='Total saldo interes mensual', required=True)
    default_dolar = fields.Float(string='Tipo de cambio $')
    total_loan_capital_bolivianos = fields.Float(string='Total saldo prestamo Bs.')
    total_balance_total_interest_month_bolivianos = fields.Float(string='Total saldo interes mensual Bs.')
    total = fields.Float(string='Total saldo Bs.', compute='_compute_total')
    partial_devolution = fields.Float(string="Devolucion")
    option_liquidation = fields.Boolean(string='Liquidar prestamo')
    option_liquidation_contributions = fields.Boolean(string="Liquidar aportes")
    def action_confirm(self):
        vals = {
            'disengagement': self.disengagement,
            'partner_payroll_ids': self.partner_payroll_id.id,
            'date_proccess': self.date_finalize,
            'total_voluntary_contributions': self.total_voluntary_contributions_certificate,
            'total_capital_initial': self.capital_initial,
        }
        total_contribution = self.total_voluntary_contributions_certificate + self.capital_initial
        total_loan = self.total_loan_capital_bolivianos + self.total_balance_total_interest_month_bolivianos
        if self.option_liquidation == True and total_contribution >= total_loan:
            vals['loan_capital_bolivianos'] = self.total_loan_capital_bolivianos
            vals['balance_interest_month_bolivianos'] = self.total_balance_total_interest_month_bolivianos
        record = self.env['finalize.contributions'].create(vals)
        if not record:
            raise UserError(_('Error al liquidar prestamo.'))



    @api.depends('total_loan_capital_bolivianos', 'total_balance_total_interest_month_bolivianos')
    def _compute_total(self):
        for record in self:
            record.total = record.total_loan_capital_bolivianos + record.total_balance_total_interest_month_bolivianos

    @api.onchange('partial_devolution')
    def onchange_partial_devolution(self):
        for record in self:
            if record.partial_devolution > record.total_contributions:
                raise ValidationError('El monto parcial no puede ser mayor al total')

    @api.onchange('option_liquidation')
    def onchange_option_liquidation(self):
        for record in self:
            record.disengagement = 0

    @api.onchange('option_liquidation_contributions')
    def onchange_option_liquidation_contributions(self):
        for record in self:
            if record.option_liquidation_contributions == True:
                record.disengagement = 10
            else:
                record.disengagement = 0
