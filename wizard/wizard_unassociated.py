from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class WizardUnassociated(models.TransientModel):
    _name = 'wizard.unassociated'

    partner_payroll_id = fields.Many2one('partner.payroll', string='Nómina de asociado', required=True)
    partner_id = fields.Char(string='Asociado', related='partner_payroll_id.partner_id.name', store=True)
    total_contributions = fields.Float(string='Total aportes', required=True)
    reafiliacion = fields.Selection([('passive_reserve_a', 'Reserva pasivo "A"'),
                                     ('passive_reserve_b', 'Reserva pasivo "B"'),
                                     ('unassociated','No asociado')],
                                    string='Reafiliación', required=True)
    date = fields.Date(string='Fecha', required=True)

    def exclude_contributions(self):
        partner_payroll = False
        for record in self:
            if record.reafiliacion == 'passive_reserve_a':
                record.partner_payroll_id.partner_status_historical = record.partner_payroll_id.partner_id.partner_status
                record.partner_payroll_id.partner_status_especific_historical = record.partner_payroll_id.partner_id.partner_status_especific
                record.partner_payroll_id.partner_id.partner_status_especific = 'passive_reserve_a'
                partner_payroll = record.env['partner.payroll'].create({
                    'partner_id': record.partner_payroll_id.partner_id.id,
                    # 'partner_status_especific': 'passive_reserve_a',
                    'date_registration': record.date,
                    'state': 'draft',
                })
            if record.reafiliacion == 'passive_reserve_b':
                record.partner_payroll_id.partner_status_historical = record.partner_payroll_id.partner_id.partner_status
                record.partner_payroll_id.partner_status_especific_historical = record.partner_payroll_id.partner_id.partner_status_especific
                record.partner_payroll_id.partner_id.partner_status_especific = 'passive_reserve_a'
                partner_payroll = record.env['partner.payroll'].create({
                    'partner_id': record.partner_payroll_id.partner_id.id,
                    # 'partner_status_especific': 'passive_reserve_b',
                    'date_registration': record.date,
                    'state': 'draft',
                })
            if record.reafiliacion == 'unassociated':
                record.partner_payroll_id.partner_id.state = record.reafiliacion
                partner_payroll = True

            if partner_payroll:
                record.partner_payroll_id.write({
                    'state': 'unassociated',
                    'contribution_total_excluded': record.total_contributions,
                    'date_unassociated': record.date,
                })

