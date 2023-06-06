from odoo import models, fields, api, _
import calendar

class Month(models.Model):

    _name = 'month'

    name = fields.Char(string='Nombre', compute='_compute_month',readonly=True)
    date_field = fields.Date(string='Fecha', required=True, default=fields.Date.today())
    month = fields.Char(string='Código', compute='_compute_month', readonly=True)
    # config_id = fields.Many2one('res.config.settings', string='Configuración')


    @api.depends('date_field')
    def _compute_month(self):
        for rec in self:
            rec.month = rec.date_field.strftime('%m')
            rec.name = calendar.month_name[rec.date_field.month]



