from xml import etree

from odoo import models, fields, api, _

class PayrollPayments(models.Model):
    _name = 'payroll.payments'
    _description = 'Pagos individuales de planilla'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Planilla de socio')
    income = fields.Float(string='Ingresos', required=True)
    mandatory_contribution_certificate = fields.Float(string='Cert. Apor. O.', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.mandatory_contribution_certificate')))
    voluntary_contribution_certificate = fields.Float(string='Cert. Apor. V.', compute="compute_voluntary_contribution_certificate", store=True)
    regulation_cup = fields.Float(string='Taza Regulación', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.regulation_cup')))
    miscellaneous_income = fields.Float(string='Ingresos diversos', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income')))
    payment_date = fields.Datetime(string='Fecha de pago', default=fields.Datetime.now())
    period_register = fields.Char(string='Periodo de registro', compute="compute_period_register", store=True)
    state = fields.Selection(
        [('draft', 'Borrador'), ('transfer', 'Transferencia bancaria'), ('ministry_defense', 'Ministerio de defensa')],
        default='draft')
    capital = fields.Float(string='Capital')
    interest = fields.Float(string='Interes')

    @api.depends('payment_date')
    def compute_period_register(self):
        for record in self:
            record.period_register = record.payment_date.strftime('%m') + '/' + record.payment_date.strftime('%Y')


    @api.model
    def create(self, vals_list):
        name = self.env['ir.sequence'].next_by_code('payroll.payments')
        vals_list['name'] = name
        res = super(PayrollPayments, self).create(vals_list)
        return res

    def open_one2many_line(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Model Title',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

    @api.depends('income', 'mandatory_contribution_certificate', 'miscellaneous_income','regulation_cup')
    def compute_voluntary_contribution_certificate(self):
        for record in self:
            record.voluntary_contribution_certificate = record.income - record.mandatory_contribution_certificate - record.miscellaneous_income - record.regulation_cup

    def confirm_payroll(self):
        self.state = 'transfer'


