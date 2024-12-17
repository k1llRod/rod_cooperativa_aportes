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
                total_income = 0
                total_miscellaneous_income = 0
                total_regulation_cup = 0
                total_mandatory_contribution_certificate = 0
                total_voluntary_contribution_certificate = 0
                total_other_contribution = 0
                for rec in record.partner_payroll_id.payroll_payments_ids.filtered(lambda x:x.state != 'no_contribution' and x.state != 'draft'):
                    total_income += rec.income
                    total_miscellaneous_income += rec.miscellaneous_income
                    total_regulation_cup += rec.regulation_cup
                    total_mandatory_contribution_certificate += rec.mandatory_contribution_certificate
                    total_voluntary_contribution_certificate += rec.voluntary_contribution_certificate
                    total_other_contribution += rec.other_contribution
                create_payroll = record.partner_payroll_id.payroll_payments_ids.create({
                    'income': -(total_income),
                    'income_passive': 0,
                    'miscellaneous_income': -(total_miscellaneous_income),
                    'regulation_cup': -(total_regulation_cup),
                    'mandatory_contribution_certificate': -(total_mandatory_contribution_certificate),
                    'voluntary_contribution_certificate': -(total_voluntary_contribution_certificate),
                    'other_contribution': -(total_other_contribution),
                    'state': 'partner_return'
                })
                record.partner_payroll_id.partner_id.state = record.reafiliacion
                partner_payroll = True


            if partner_payroll:
                record.partner_payroll_id.write({
                    'state': 'unassociated',
                    'contribution_total_excluded': record.total_contributions,
                    'date_unassociated': record.date,
                })

