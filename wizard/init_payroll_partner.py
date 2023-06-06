from odoo import models, fields, api, _

class InitPayrollPartner(models.TransientModel):
    _name = 'init.payroll.partner'

    # Campos del wizard
    partner_payroll_id = fields.Integer(string='Partner payroll id', required=True)
    capital_minimum = fields.Integer(string='Capital mínimo', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.capital_minimum')))
    capital_base = fields.Float(string='Capital base', required=True)

    def action_confirm(self):
        # Acciones a realizar cuando se hace clic en el botón
        # Puedes agregar aquí la lógica que deseas ejecutar al confirmar el wizard
        # Por ejemplo, crear un registro en otro modelo con los valores del wizard

        # Código de ejemplo:
        partner_payroll = self.env['partner.payroll'].browse(self.partner_payroll_id)
        partner_payroll.capital_base = self.capital_base
        partner_payroll.state = 'process'
        partner_payroll.date_burn_partner = fields.Datetime.now()
        return True
