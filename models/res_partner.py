from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
class ResPartner(models.Model):
    _inherit = 'res.partner'

    state = fields.Selection([('draft', 'Borrador'), ('verificate', 'Verificación'), ('activate', 'Socio activo'),
                              ('rejected', 'Rechazado')],
                             string='Estado', default='draft', track_visibility='onchange')
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
            if not self.code_contact:
                raise ValidationError(_('Debe ingresar el código de contacto'))
            if not self.partner_status_especific:
                raise ValidationError(_('Debe ingresar la situación del socio'))
            if not self.ci_photocopy:
                raise ValidationError(_('Debe ingresar la Fotocopía de la cédula de identidad'))
            if not self.photocopy_military_ci:
                raise ValidationError(_('Debe ingresar la Fotocopia de la  cédula militar'))
            self.state = 'verificate'

    def approve_partner(self):
        self.ensure_one()
        if self.state == 'verificate':
            self.state = 'activate'


    def return_form(self):
        self.ensure_one()
        if self.state == 'verificate':
            self.state = 'draft'





