from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

class HomolagateForm(models.TransientModel):
    _name = 'homolagate.form'

    # Campos del wizard
    date_field = fields.Date(string='Fecha', required=True, default=fields.Date.today())
    month = fields.Char(string='Mes', compute='compute_period',readonly=True)
    year = fields.Char(string='Año', compute='compute_period',readonly=True)
    period = fields.Char(string='Periodo')
    count_period = fields.Integer(string='Registros anteriores')
    count_register_reconciled = fields.Integer(string='Registros para conciliar')
    @api.depends('date_field')
    def compute_period(self):
        for record in self:
            record.month = record.date_field.strftime('%m')
            record.year = record.date_field.strftime('%Y')
            period = record.month + '/' + record.year
            record.count_period = len(self.env['nominal.relationship.mindef.contributions'].search([('period_process','=',period)]))
            record.count_register_reconciled = len(self.env['nominal.relationship.mindef.contributions'].search([('period_process','=',False)]))

    def homolagate(self):
        filing_cabinet_ids = self.env['nominal.relationship.mindef.contributions'].search(
            [('period_process', '=', False),('state','!=','reconciled')])
        period = self.month + '/' + self.year
        for rec in filing_cabinet_ids:
            rec.period_process = period
            # rec.write({'period_process': self.month + '/' + self.year})
            rec.date_process = self.date_field
            rec.state = 'draft'
        context = {'default_message': 'Se han homologado ' + str(len(filing_cabinet_ids)) + ' del periodo ' + period + ' con éxito.'}
        return {
            'name': 'Registros conciliados',
            'type': 'ir.actions.act_window',
            'res_model': 'alert.message',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }
        

    def show_alert_wizard(self):
        context = {'custom_message': 'Este es un mensaje personalizado.'}
        action = self.env.ref('rod_cooperativa_aportes.alert_wizard_action').read()[0]
        action['context'] = context
        return action





