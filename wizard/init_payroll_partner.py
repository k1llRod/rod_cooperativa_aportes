from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime

class InitPayrollPartner(models.TransientModel):
    _name = 'init.payroll.partner'

    # Campos del wizard
    partner_payroll_id = fields.Integer(string='Partner payroll id', required=True)
    capital_minimum = fields.Integer(string='Capital mínimo', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.capital_minimum')))
    capital_base = fields.Float(string='Capital base', required=True)
    date_register = fields.Datetime(string='Fecha de registro', default=fields.Datetime.now())

    def calculate_month_difference(self):
        if self.date_register:
            difference = relativedelta(datetime.today(), self.date_register)
            month_difference = difference.months + (difference.years * 12)
            return month_difference
        return 0

    def action_confirm(self):
        # Acciones a realizar cuando se hace clic en el botón
        # Puedes agregar aquí la lógica que deseas ejecutar al confirmar el wizard
        # Por ejemplo, crear un registro en otro modelo con los valores del wizard

        partner_payroll = self.env['partner.payroll'].browse(self.partner_payroll_id)
        partner_payroll.capital_base = self.capital_base
        partner_payroll.state = 'process'
        partner_payroll.date_burn_partner = self.date_register
        make_register = self.calculate_month_difference()
        date = self.date_register
        for i in range(make_register):
            partner_payroll.payroll_payments_ids = [
                (0, 0, {'payment_date': date, 'income': 0,
                        'state': 'draft',
                        })]
            date = date + relativedelta(months=1)
        return True
