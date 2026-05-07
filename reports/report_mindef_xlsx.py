from odoo import models


class MindefReportXlsx(models.AbstractModel):
    _name = 'report.rod_cooperativa_aportes.report_mindef_xlsx_abstract'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Planilla Homologación')

        # --- ESTILOS ---
        title_style = workbook.add_format(
            {'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#4F81BD', 'font_color': 'white'})
        header_style = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9E1F2', 'align': 'center'})
        sub_title_style = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
        data_style = workbook.add_format({'border': 1})
        money_style = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        center_style = workbook.add_format({'border': 1, 'align': 'center'})

        # --- ENCABEZADO ---
        sheet.merge_range('A1:G1', 'PLANILLA DE HOMOLOGACIÓN MINDEF', title_style)
        sheet.write('A2', 'Periodo:', sub_title_style)
        sheet.write('B2', data.get('period'), data_style)
        sheet.write('A3', 'Fecha:', sub_title_style)
        sheet.write('B3', data.get('date'), data_style)

        row = 5

        # Definición de las secciones (Estado, IDs, Color de fondo)
        sections = [
            ('BORRADOR (Draft)', data.get('ids_draft'), '#D9E1F2'),
            ('NO CONCILIADOS', data.get('ids_no_reconciled'), '#FCE4D6'),
            ('CONCILIADOS', data.get('ids_reconciled'), '#E2EFDA'),
            ('OBSERVADOS', data.get('ids_observed'), '#FFF2CC'),
        ]

        for title, ids, color in sections:
            if not ids:
                continue

            # Título de la sección
            section_style = workbook.add_format({'bold': True, 'bg_color': color, 'border': 1})
            sheet.merge_range(row, 0, row, 6, f"ESTADO: {title} - Total: {len(ids)}", section_style)
            row += 1

            # Encabezados de tabla (Agregamos "N°")
            headers = ['N°', 'Grado', 'Mención', 'Nombre Completo', 'Monto (Bs)', 'Gestión', 'Mes']
            for col, text in enumerate(headers):
                sheet.write(row, col, text, header_style)
            row += 1

            # Reiniciamos el contador para cada sección
            counter = 1
            records = self.env['nominal.relationship.mindef.contributions'].browse(ids)

            for rec in records:
                sheet.write(row, 0, counter, center_style)  # Imprimimos el N°
                sheet.write(row, 1, rec.degree or '', data_style)
                sheet.write(row, 2, rec.mension or '', data_style)
                sheet.write(row, 3, rec.name_complete or '', data_style)
                sheet.write(row, 4, rec.amount_bs or 0.0, money_style)
                sheet.write(row, 5, rec.management or '', data_style)
                sheet.write(row, 6, rec.month or '', data_style)

                row += 1
                counter += 1  # Incrementamos el contador

            row += 2  # Espacio de separación entre cuadros

        # Ajuste de anchos de columna
        sheet.set_column('A:A', 5)  # Columna del contador
        sheet.set_column('B:C', 15)
        sheet.set_column('D:D', 40)  # Nombre
        sheet.set_column('E:G', 12)