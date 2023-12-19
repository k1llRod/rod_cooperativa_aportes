from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    regulation_cup = fields.Float(string='Taza Regulación %')
    mandatory_contribution_certificate = fields.Float(string='Cert. Apor. O.')
    # voluntary_contribution_certificate = fields.Float(string='Cert. Apor. V.')
    miscellaneous_income = fields.Float(string='Ingresos diversos')
    certified_period = fields.Integer(string='Periodo certificado')
    capital_minimum = fields.Integer(string='Capital mínimo')
    month_ids = fields.Many2many('month', string='Meses')
    contribution_passive = fields.Float(string='Aporte pasivo')
    account_income_id = fields.Many2one('account.account', string='Ingreso')
    account_inscription_id = fields.Many2one('account.account', string='Inscripcion')
    account_regulation_cup_id = fields.Many2one('account.account', string='Tasa de regulacion')
    account_mandatory_contribution_id = fields.Many2one('account.account', string='Aportes obligatorios')
    account_voluntary_contribution_id = fields.Many2one('account.account', string='Aportes voluntarios')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        regulation_cup=float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.regulation_cup'))
        mandatory_contribution_certificate=self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.mandatory_contribution_certificate')
        miscellaneous_income=self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income')
        certified_period=self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.certified_period')
        capital_minimum=self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.capital_minimum')
        month_ids=self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.month_ids')
        contribution_passive = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.contribution_passive')
        account_income_id = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_income_id')
        account_inscription_id = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_inscription_id')
        account_regulation_cup_id = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_regulation_cup_id')
        account_mandatory_contribution_id = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_mandatory_contribution_id')
        account_voluntary_contribution_id = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_voluntary_contribution_id')

        res.update(
            regulation_cup=regulation_cup,
            mandatory_contribution_certificate=mandatory_contribution_certificate,
            miscellaneous_income=miscellaneous_income,
            certified_period=certified_period,
            capital_minimum=capital_minimum,
            month_ids=[(6, 0, literal_eval(month_ids))] if month_ids else [(6, 0, '')],
            contribution_passive=contribution_passive,
            account_income_id=account_income_id,
            account_inscription_id=account_inscription_id,
            account_regulation_cup_id=account_regulation_cup_id,
            account_mandatory_contribution_id=account_mandatory_contribution_id,
            account_voluntary_contribution_id=account_voluntary_contribution_id,
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.regulation_cup', self.regulation_cup)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.mandatory_contribution_certificate', self.mandatory_contribution_certificate)
        # self.env['ir.config_parameter'].sudo().set_param('voluntary_contribution_certificate', self.voluntary_contribution_certificate)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.miscellaneous_income', self.miscellaneous_income)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.certified_period', self.certified_period)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.capital_minimum', self.capital_minimum)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.month_ids', self.month_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.contribution_passive',self.contribution_passive)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.account_income_id',self.account_income_id.id)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.account_inscription_id',self.account_inscription_id.id)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.account_regulation_cup_id',self.account_regulation_cup_id.id)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.account_mandatory_contribution_id',self.account_mandatory_contribution_id.id)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa_aportes.account_voluntary_contribution_id',self.account_voluntary_contribution_id.id)
        return res


