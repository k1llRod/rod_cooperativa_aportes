from odoo import models, fields, api, _


class AlertMessage(models.TransientModel):
    _name = 'alert.message'

    # Campos del wizard
    message = fields.Char(string='Mensaje', required=True)
    title = fields.Char(string='Título', required=True)

    # @api.model
    # def default_get(self, fields):
    #     res = super(AlertMessage, self).default_get(fields)
    #     # Obtén el valor del argumento enviado al crear el wizard
    #     context = self.env.context
    #     message = context.get('custom_message', 'Este es un mensaje de alerta.')
    #     res['message'] = message
    #     return res

    def confirm(self):
        # Realiza las acciones que desees al confirmar el wizard
        return {'type': 'ir.actions.act_window_close'}