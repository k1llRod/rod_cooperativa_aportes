from odoo import models, fields, api, _

class FinalizeContributions(models.Model):
    _name = 'finalize.contributions'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo')
    date_proccess = fields.Date(string='Fecha de proceso')
    partner_payroll_ids = fields.Many2one('partner.payroll', string='Aportes')
    disengagement = fields.Float('Desvinculacion')
    total_mandatory_contributions = fields.Float(string='Total de aportes obligatorios')
    total_voluntary_contributions = fields.Float(string='Total de aportes voluntarios')
    total_capital_initial = fields.Float('Total capital inicial')
    total_voluntary = fields.Float('Total aportes', compute='calculate_total_voluntary')


    loan_capital_bolivianos = fields.Float(string='Total capital prestamo')
    balance_interest_month_bolivianos = fields.Float(string='Total dias de interes')

    account_voluntary_contributions = fields.Many2one('account.account', string='Aportes voluntarios')

    account_capital_loan = fields.Many2one('account.account', string='Capital credito')
    account_interest_month = fields.Many2one('account.account', string='Interes mensual')

    @api.depends('total_voluntary_contributions','total_capital_initial')
    def calculate_total_voluntary(self):
        for record in self:
            total = record.total_voluntary_contributions + record.total_capital_initial
            record.total_voluntary = total


    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('finalize.contributions')
        vals['name'] = name
        res = super(FinalizeContributions, self).create(vals)
        return res

    def open_finalize_contributions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Liquidacion de aportes'),
            'res_model': 'finalize.contributions',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
