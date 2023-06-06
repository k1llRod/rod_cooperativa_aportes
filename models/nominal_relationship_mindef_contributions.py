from odoo import models, fields, api, _



class NominalRelationshipMindefContributions(models.Model):
    _name = 'nominal.relationship.mindef.contributions'
    _description = 'Relacion nominal aportes mindef'

    name = fields.Char(string='N')
    organism = fields.Char(string='Organismo')
    eit_item = fields.Char(string='Item EIT')
    ci = fields.Char(string='CI')
    degree = fields.Char(string='Grado')
    mension = fields.Char(string='Mension')
    name_complete = fields.Char(string='Nombre completo')
    amount_bs = fields.Float(string='Monto Bs')
    amount_usd = fields.Float(string='Monto USD')
    date_register = fields.Date(string='Fecha de registro', default=fields.Date.today())
    date_process = fields.Date(string='Fecha de proceso')
    period_process = fields.Char(string='Periodo de proceso')
    state = fields.Selection([('draft', 'Borrador'), ('no_reconciled', 'No conciliado'), ('reconciled', 'Conciliado'),
                              ('observed', 'Observado')], string='Estado')

    def homologate_data_mindef(self):
        return {
            'name': 'Homologar información',
            'type': 'ir.actions.act_window',
            'res_model': 'homolagate.form',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }