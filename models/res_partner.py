from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    state = fields.Selection([('draft', 'Borrador'), ('verificate', 'Verificación'), ('activate', 'Socio activo'),
                              ('rejected', 'Rechazado'), ('unsubscribe', 'Baja')],
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
    loan_count = fields.Integer(string='Préstamos', compute='compute_contributions_count')
    date_unsubscribe = fields.Date(string='Fecha de baja')

    def compute_contributions_count(self):
        for record in self:
            contributions = len(record.env['partner.payroll'].search([('partner_id', '=', record.id)]))
            loans = len(record.env['loan.application'].search([('partner_id', '=', record.id)]))
            record.contributions_count = contributions
            record.loan_count = loans





    def action_view_contributions(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa_aportes.action_partner_payroll")
        action['domain'] = [
            ('partner_id.id', '=', self.id),
        ]
        return action

    def action_view_loans(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa.action_loan_application")
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

    def init_loan(self):
        loan_application = self.env['loan.application'].create({'partner_id': self.id,
                                                                'date_application': datetime.now(),
                                                                'type_loan': 'regular',
                                                                })
        return {
            'name': 'Detalle del prestamo',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.application',
            'res_id': loan_application.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def init_massive_payment(self):
        partners_off = self.env['partner.payroll'].search([])
        domain = []
        for partner in partners_off:
            domain.append(partner.partner_id.id)
        partners_init = self.filtered(lambda x:x.id not in domain)
        for rec in partners_init:
            rec.init_partner()

    def unsubscribe(self):
        self.ensure_one()
        verificate_contribution = self.env['partner.payroll'].search([('partner_id','=',self.id)])
        if verificate_contribution.state != 'finalized':
            raise ValidationError(_('No se puede dar de baja a un socio que tiene aportes registrados'))
        self.date_unsubscribe = datetime.now()
        self.state = 'unsubscribe'

