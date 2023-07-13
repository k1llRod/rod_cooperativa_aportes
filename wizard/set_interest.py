from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


class SetInteres(models.TransientModel):
    _name = 'set.interes'
    _description = 'Asignar intereses'

    name = fields.Char(string="Gestion", compute="compute_period")
    
    index = fields.Float(string="Indice", digits=(16,4))
    date_field_select = fields.Date(string="Fecha", require=True, default=fields.Date.today())
    yield_amount = fields.Float(string="Monto de rendimiento", compute="compute_yield_amount")
    partner_payroll_id = fields.Many2one('partner.payroll', string="Socio")
    contributions_total = fields.Float(string="Total aportes", related="partner_payroll_id.contribution_total")

    def action_asignement_interest(self):
        vals = {
            'name': self.name,
            'management_date': self.date_field_select,
            'index': self.index,
            'yield_amount': self.yield_amount,
            'partner_payroll_id': self.partner_payroll_id.id,
            'contributions_total': self.contributions_total,
            'management': self.name,
        }
        res = self.env['performance.management'].create(vals)
        if res:
            self.partner_payroll_id.message_post(body="Interes anual de aportes registrado: " + str(self.yield_amount))
        else:
            raise ValidationError("Error al registrar interes anual de aportes")


    @api.depends('date_field_select')
    def compute_period(self):
        for record in self:
            if record.date_field_select == False:
                record.name = 'Seleccionar fecha'
            else:
                record.name = record.date_field_select.strftime('%Y')
    @api.depends('index')
    def compute_yield_amount(self):
        for record in self:
            if record.index == False:
                record.yield_amount = 0
            else:
                record.yield_amount = record.contributions_total * record.index