from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class WizardUnassociated(models.TransientModel):
    _name = 'wizard.unassociated'

    partner_payroll_id = fields.Many2one('partner.payroll', string='Nómina de asociado', required=True)
    partner_id = fields.Char(string='Asociado', related='partner_payroll_id.partner_id.name', store=True)
    total_contributions = fields.Float(string='Total aportes', required=True)
    reafiliacion = fields.Selection([('passive_reserve_a', 'Reserva pasivo "A"'),
                                     ('passive_reserve_b', 'Reserva pasivo "B"')],
                                    string='Reafiliación')
    date = fields.Date(string='Fecha')

    def exclude_contributions(self):
        for record in self:
            if record.reafiliacion == 'passive_reserve_a':
                payroll_partner = record.env['partner.payroll'].create({
                    'partner_id': record.partner_payroll_id.partner_id.id,
                    'partner_status': 'passive_reserve_a',
                    'date_registration': record.date,
                    'state': 'draft',
                })
            if record.reafiliacion == 'passive_reserve_b':
                partner_payroll = record.env['partner.payroll'].create({
                    'partner_id': record.partner_payroll_id.partner_id.id,
                    'partner_status': 'passive_reserve_b',
                    'date_registration': record.date,
                    'state': 'draft',
                })
            if partner_payroll:
                record.partner_payroll_id.write({
                    'state': 'unassociated',
                    'total_contributions': record.total_contributions,
                })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'partner.payroll',
            'view_mode': 'form',
            'res_id': self.partner_payroll_id.id,
            'target': 'current',
        }

