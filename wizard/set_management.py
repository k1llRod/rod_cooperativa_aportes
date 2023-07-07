from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


class SetManagement(models.TransientModel):
    _name = 'set.management'
    _description = 'Asignar rendimiento a los socios'

    name = fields.Char(string="Gestion", compute="compute_set_management")
    set_management_id = fields.Many2one('performance_index.log', string="Indice rendimiento")

    count_partner = fields.Integer(string="Cantidad de socios", compute="compute_count_partner")
    count_partner_cat_b = fields.Integer(string="Cantidad de socios categoria B")
    index = fields.Float(string="Indice", digits=(16,4), compute="compute_set_management")
    date_field_select = fields.Date(string="Fecha", require=True, default=fields.Date.today())


    def action_asignement_management(self):
        self.ensure_one()
        if self.date_field_select:
            self.date_field_select = datetime.strptime(self.date_field_select, "%Y-%m-%d").date()
        else:
            raise UserError(_("Debe seleccionar una fecha"))

    @api.depends('set_management_id')
    def compute_set_management(self):
        for record in self:
            record.name = record.set_management_id.name
            record.index = record.set_management_id.index

    def compute_count_partner(self):
        for record in self:
            record.count_partner = self.env['partner.payroll'].search_count([('partner_status_especific', '=', 'acive_service')])



