from odoo import models, fields, api, _



class NominalRelationshipMindefContributions(models.Model):
    _name = 'nominal.relationship.mindef.contributions'
    _description = 'Relacion nominal aportes mindef'

    name = fields.Char(string='N')
    management = fields.Char(string='Gestion')
    month = fields.Char(string='Mes')
    supporting_document = fields.Char(string='Documento respaldo')
    eit_codorg = fields.Char(string='eit_codorg')
    eit_codrep = fields.Char(string='eit_codrep')
    distribution = fields.Char(string='Reparticion')
    group = fields.Char(string='Grupo')
    group_description = fields.Char(string='Descripcion del grupo')
    identification = fields.Char(string='Identificador')
    creditor = fields.Char(string='Acreedor')
    code_concept = fields.Char(string='Codigo concepto')
    code_creditor = fields.Char(string='Codigo acreedor')
    bank_account = fields.Char(string='Cuenta bancaria')
    personal_code = fields.Char(string='Codigo personal')

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