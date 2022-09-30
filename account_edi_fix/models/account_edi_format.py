# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.pdf import OdooPdfFileReader, OdooPdfFileWriter
from odoo.osv import expression

from lxml import etree
import base64
import io
import logging

_logger = logging.getLogger(__name__)


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _embed_edis_to_pdf(self, pdf_content, invoice):
        """ Create the EDI document of the invoice and embed it in the pdf_content.

        :param pdf_content: the bytes representing the pdf to add the EDIs to.
        :param invoice: the invoice to generate the EDI from.
        :returns: the same pdf_content with the EDI of the invoice embed in it.
        """
        print("account_edi_fix ===>>> _embed_edis_to_pdf")
        attachments = []
        for edi_format in self:
            attachment = invoice._get_edi_attachment(edi_format)
            if attachment and edi_format._is_embedding_to_invoice_pdf_needed():
                datas = base64.b64decode(attachment.with_context(bin_size=False).datas)
                attachments.append({'name': attachment.name, 'datas': datas})

        if attachments:
            # Add the attachments to the pdf file
            reader_buffer = io.BytesIO(pdf_content)
            reader = OdooPdfFileReader(reader_buffer, strict=False)
            writer = OdooPdfFileWriter()
            writer.cloneReaderDocumentRoot(reader)
            for vals in attachments:
                writer.addAttachment(vals['name'], vals['datas'])
            buffer = io.BytesIO()
            writer.write(buffer)
            pdf_content = buffer.getvalue()
            reader_buffer.close()
            buffer.close()
        return pdf_content

   