from odoo import models, fields, api, _


class PartnerPayroll(models.Model):
    _name = 'partner.payroll'
    _description = 'Planilla de socio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    state = fields.Selection([('draft', 'Borrador'), ('process', 'En proceso'), ('finalized', 'Finalizado')],
                             default='draft')
    partner_id = fields.Many2one('res.partner', string='Socio')
    partner_status = fields.Selection([('activate', 'Servicio activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive_reserve_a', 'Reserva pasivo "A"'),
                                       ('passive_reserve_b', 'Reserva pasivo "B"')],
                                      string='Situación de socio', related='partner_id.partner_status', readonly=True)
    date_registration = fields.Datetime(string='Fecha de registro')
    date_burn_partner = fields.Datetime(string='Fecha de alta')
    total_contribution = fields.Float(string='Total aportado')
    advanced_payments = fields.Float(string='Pagos adelantados')
    payroll_payments_ids = fields.One2many('payroll.payments', 'partner_payroll_id', string='Pagos individuales',
                                           tracking=True)
    capital_base = fields.Float(string='Capital base', store=True, tracking=True)
    capital_total = fields.Float(string='Capital total', compute="compute_capital_total",store=True)
    interest_total = fields.Float(string='Interes total', store=True)
    miscellaneous_income = fields.Float(string='Gastos adicional', compute="compute_miscellaneous_income")
    total = fields.Float(string='Total', store=True)

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('partner.payroll')
        vals['name'] = name
        res = super(PartnerPayroll, self).create(vals)
        return res

    def init_payroll_partner_wizard(self):
        # Acción para abrir el wizard
        # Puedes personalizar esta función según tus necesidades
        record_id = self.id
        context = {
            'default_partner_payroll_id': record_id,
            'default_capital_base': self.capital_base,
        }
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'init.payroll.partner',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }
    @api.depends('payroll_payments_ids')
    def compute_capital_total(self):
        for record in self:
            for rec in record.payroll_payments_ids:
                record.capital_total = sum(record.payroll_payments_ids.mapped('voluntary_contribution_certificate'))

    def import_payroll(self):
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'reconcile.contributions',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }
    @api.depends('partner_id')
    def compute_partner_status(self):
        for record in self:
            record.partner_status = record.partner_id.status

    @api.depends('payroll_payments_ids')
    def compute_miscellaneous_income(self):
        miscellaneous_income = float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income'))
        for record in self:
            if record.state != 'draft':
                if record.payroll_payments_ids.filtered(lambda x: x.miscellaneous_income == miscellaneous_income and (x.state == 'ministry_defense' or x.state == 'transfer')):
                    record.miscellaneous_income = miscellaneous_income - float(record.payroll_payments_ids.mapped('miscellaneous_income')[0])
                else:
                    record.miscellaneous_income = miscellaneous_income
            else:
                record.miscellaneous_income = miscellaneous_income