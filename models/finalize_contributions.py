from odoo import models, fields, api, _

class FinalizeContributions(models.Model):
    _name = 'finalize.contributions'
    _description = 'Finalize Contributions'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo', required=True)
    partner_payroll_id = fields.Many2one('partner.payroll', string='Codigo Aporte')
    date_finalize = fields.Date(string='Fecha de Finalizacion')
    disengagement = fields.Float(string='Desvinculacion', required=True, default=10)
    total_mandatory_contributions_certificate = fields.Float(string='Total de aportes obligatorios', required=True)
    total_voluntary_contributions_certificate = fields.Float(string='Total de aportes voluntarios', required=True)
    total_other_contributions = fields.Float(string='Total de otros aportes', required=True)
    total_performance_contributions = fields.Float(string='Total rendimiento de aportes', required=True)
    total_loan_capital = fields.Float(string='Total saldo de prestamo $')
    total_balance_total_interest_month = fields.Float(string='Total saldo interes mensual')
    default_dolar = fields.Float(string='Dolar $')
    total_loan_capital_bolivianos = fields.Float(string='Total saldo prestamo Bs.')
    total_balance_total_interest_month_bolivianos = fields.Float(string='Total saldo interes mensual Bs.')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Realizado'),
    ], string='Estado', default='draft')

    accounting_finalize_contributions_id = fields.Many2one('account.move', string='Asiento contable')
    accounting_finalize_contributions_state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
    ], string='Estado', default='draft', related='accounting_finalize_contributions_id.state', store=True,
        track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', string='Diario')
    account_contributions_id = fields.Many2one('account.account', string='Cuenta de aportes')

    reafiliation = fields.Selection([
        ('passive_reserve_a','Pasivo categoria "A"'),
        ('passive_reserve_b','Pasivo categoria "B"')
        ], string='Reafiliacion como')
    partner_status_reafiliation = fields.Selection([('active', 'Activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive', 'Servicio pasivo'),
                                       ], string="Situacion general",
                                        store=True)





    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('finalize.contributions')
        return super(FinalizeContributions, self).create(vals)


    def finalize_contributions(self):
        # Here you can write the code to finalize the contributions
        return True

    def open_finalize_contributions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Liquidacion de aportes'),
            'res_model': 'finalize.contributions',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        for record in self:
            if record.partner_payroll_id.state == 'process_finalized':
                record.partner_payroll_id.partner_status_especific_historical = record.partner_payroll_id.partner_status_especific
                record.partner_payroll_id.partner_status_historical = record.partner_payroll_id.partner_status
                create = self.env['partner.payroll'].create({
                    'partner_id': record.partner_payroll_id.partner_id.id,
                    # 'date': record.date_finalize,
                    # 'state': 'process',
                    'partner_status_especific_historical': record.reafiliation,
                    'partner_status_historical': record.partner_status_reafiliation,
                })
                if create:
                    record.partner_payroll_id.partner_id.partner_status_especific = record.reafiliation
                    record.state = 'done'
                    record.partner_payroll_id.state = 'finalized'
                    record.partner_payroll_id.state_finalize = 'hecho'
                    if record.partner_payroll_id.type_disengagement == 'fallecimiento':
                        record.partner_payroll_id.partner_id.state = 'deceased'
                    if record.partner_payroll_id.type_disengagement == 'retiro_voluntario':
                        record.partner_payroll_id.partner_id.state = 'unsubscribed'


