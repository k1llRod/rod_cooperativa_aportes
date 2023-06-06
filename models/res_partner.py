from odoo import models, fields, api, _
from datetime import datetime, timedelta
class ResPartner(models.Model):
    _inherit = 'res.partner'

    def init_partner(self):
        partner_payroll = self.env['partner.payroll'].create({'partner_id': self.id,
                                            'date_registration': datetime.now(),
                                            'total_contribution': 0,
                                            'advanced_payments': 0,
                                            'state': 'draft'})
        view_id = self.env.ref('rod_cooperativa_aportes.action_partner_payroll')
        return {
            'name': 'Detalle del Registro',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.payroll',
            'res_id': partner_payroll.id,
            'view_mode': 'form',
            'target': 'current',
        }

    contributions_count = fields.Integer(string='Aportes', compute='compute_contributions_count')
    def compute_contributions_count(self):
        contributions = len(self.env['partner.payroll'].search([('partner_id', '=', self.id)]))
        for record in self:
            record.contributions_count = contributions

    def action_view_contributions(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa_aportes.action_partner_payroll")
        action['domain'] = [
            ('partner_id.id', '=', self.id),
        ]
        return action

    def approve_verification(self):
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'activate'

    def verificate(self):
        return 1





