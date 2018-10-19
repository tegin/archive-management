from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestArchiveManagementSystem(TransactionCase):
    def setUp(self):
        super().setUp()
        self.repo = self.env['archive.repository'].create({
            'name': 'Repo',
            'model_ids': [(4, self.browse_ref('base.model_res_partner').id)],
        })
        self.location_01 = self.env['archive.location'].create({
            'description': 'LOC1'
        })
        self.location_02 = self.env['archive.location'].create({
            'description': 'LOC2'
        })
        self.file_01 = self.env['archive.file'].create({
            'repository_id': self.repo.id,
        })
        self.file_02 = self.env['archive.file'].create({
            'repository_id': self.repo.id,
        })
        self.file_03 = self.env['archive.file'].create({
            'repository_id': self.repo.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner'
        })
        self.archiving_partner = self.env['res.partner'].create({
            'name': 'Archiving user',
        })

    def new_document(self, partner=False):
        if not partner:
            partner = self.partner
        action = self.env['archive.document.add'].new({
            'repository_id': self.repo.id,
            'model': partner._name,
            'res_id': partner.id
        })
        self.assertIn(self.repo, action.repository_ids)
        action = action.create(action._convert_to_write(action._cache))
        doc = self.env['archive.document'].browse(action.run()['res_id'])
        self.assertEqual(doc.res, partner)
        return doc

    def test_document_moves(self):
        document = self.new_document()
        self.assertFalse(document.file_id)
        self.assertFalse(document.partner_id)
        self.env['archive.document.transfer.wizard'].create({
            'transfer_type': 'file',
            'document_id': document.id,
            'dest_file_id': self.file_01.id,
        }).run()
        self.assertEqual(document.file_id, self.file_01)
        self.assertFalse(document.partner_id)
        self.env['archive.document.transfer.wizard'].create({
            'transfer_type': 'partner',
            'document_id': document.id,
            'dest_partner_id': self.archiving_partner.id,
        }).run()
        self.assertFalse(document.file_id)
        self.assertEqual(document.partner_id, self.archiving_partner)

    def test_document_destruction(self):
        document = self.new_document()
        self.env['archive.document.transfer.wizard'].create({
            'transfer_type': 'file',
            'document_id': document.id,
            'dest_file_id': self.file_01.id,
        }).run()
        self.file_01.destroy()
        self.assertTrue(document.destruction_date)

    def test_destruction(self):
        self.assertTrue(self.file_01.active)
        self.assertTrue(self.file_02.active)
        self.assertTrue(self.file_03.active)
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'file',
            'file_id': self.file_02.id,
            'dest_file_id': self.file_03.id,
        }).run()
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'file',
            'file_id': self.file_01.id,
            'dest_file_id': self.file_02.id,
        }).run()
        self.file_02.destroy()
        self.assertFalse(self.file_02.active)
        self.assertFalse(self.file_01.active)
        self.assertTrue(self.file_03.active)

    def test_move(self):
        self.assertTrue(self.file_01.parent_ids)
        self.assertFalse(self.file_01.file_id)
        self.assertFalse(self.file_01.location_id)
        self.assertFalse(self.file_01.partner_id)
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'file',
            'file_id': self.file_01.id,
            'dest_file_id': self.file_02.id,
        }).run()
        self.assertEqual(self.file_01.file_id, self.file_02)
        self.assertFalse(self.file_01.location_id)
        self.assertFalse(self.file_01.partner_id)
        self.assertFalse(self.file_01.current_location_id)
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'file',
            'file_id': self.file_02.id,
            'dest_location_id': self.location_01.id,
        }).run()
        self.assertEqual(self.file_01.current_location_id, self.location_01)
        self.assertFalse(self.file_01.location_id)
        self.assertFalse(self.file_01.partner_id)
        self.assertEqual(self.file_02.current_location_id, self.location_01)
        self.assertEqual(self.file_02.location_id, self.location_01)
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'file',
            'file_id': self.file_01.id,
            'dest_location_id': self.location_02.id,
        }).run()
        self.assertFalse(self.file_01.file_id)
        self.assertFalse(self.file_01.partner_id)
        self.assertEqual(self.file_01.location_id, self.location_02)
        self.assertEqual(self.file_01.current_location_id, self.location_02)
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'file',
            'file_id': self.file_01.id,
            'dest_partner_id': self.archiving_partner.id,
        }).run()
        self.assertFalse(self.file_01.file_id)
        self.assertEqual(self.file_01.partner_id, self.archiving_partner)
        self.assertFalse(self.file_01.location_id)

    def test_repository_constrains(self):
        self.assertTrue(self.repo.active)
        with self.assertRaises(ValidationError):
            self.repo.toggle_active()
        self.file_01.destroy()
        self.file_02.destroy()
        self.file_03.destroy()
        self.repo.toggle_active()
        self.assertFalse(self.repo.active)

    def test_recursion(self):
        file = self.file_01
        new_file = self.env['archive.file'].create({
            'repository_id': self.repo.id,
        })
        for i in range(1, 10):
            self.env['archive.file.transfer.wizard'].create({
                'transfer_type': 'file',
                'file_id': file.id,
                'dest_file_id': new_file.id,
            }).run()
            file = new_file
            new_file = self.env['archive.file'].create({
                'repository_id': self.repo.id,
            })
        with self.assertRaises(ValidationError):
            self.env['archive.file.transfer.wizard'].create({
                'transfer_type': 'file',
                'file_id': file.id,
                'dest_file_id': self.file_01.id,
            }).run()

    def test_document_constrain_01(self):
        document = self.new_document()
        document_2 = self.new_document(partner=self.archiving_partner)
        transfer = self.env['archive.document.transfer'].create({
            'document_id': document_2.id,
        })
        with self.assertRaises(ValidationError):
            document._transfer(transfer)

    def test_document_constrain_02(self):
        document = self.new_document()
        document_2 = self.new_document(partner=self.archiving_partner)
        transfer = self.env['archive.document.transfer'].create({
            'document_id': document_2.id,
        })
        with self.assertRaises(ValidationError):
            document.parent_id.write({'transfer_id': transfer.id})

    def test_document_constrain_03(self):
        document = self.new_document()
        transfer = self.env['archive.document.transfer'].create({
            'document_id': document.id,
        })
        document._transfer(transfer)
        transfer_2 = self.env['archive.document.transfer'].create({
            'document_id': document.id,
            'src_file_id': self.file_01.id
        })
        with self.assertRaises(ValidationError):
            document._transfer(transfer_2)

    def test_document_constrain_04(self):
        document = self.new_document()
        transfer = self.env['archive.document.transfer'].create({
            'document_id': document.id,
        })
        document._transfer(transfer)
        transfer_2 = self.env['archive.document.transfer'].create({
            'document_id': document.id,
            'src_partner_id': self.partner.id
        })
        with self.assertRaises(ValidationError):
            document._transfer(transfer_2)

    def test_file_constrain_01(self):
        transfer = self.env['archive.file.transfer'].create({
            'file_id': self.file_02.id,
        })
        with self.assertRaises(ValidationError):
            self.file_01.parent_id.write({'transfer_id': transfer.id})

    def test_file_constrain_02(self):
        transfer = self.env['archive.file.transfer'].create({
            'file_id': self.file_02.id,
        })
        with self.assertRaises(ValidationError):
            self.file_01._transfer(transfer)

    def test_file_constrain_03(self):
        transfer = self.env['archive.file.transfer'].create({
            'file_id': self.file_01.id,
        })
        self.file_01._transfer(transfer)
        transfer_2 = self.env['archive.file.transfer'].create({
            'file_id': self.file_01.id,
            'src_partner_id': self.partner.id
        })
        with self.assertRaises(ValidationError):
            self.file_01._transfer(transfer_2)

    def test_file_constrain_04(self):
        transfer = self.env['archive.file.transfer'].create({
            'file_id': self.file_01.id,
        })
        self.file_01._transfer(transfer)
        transfer_2 = self.env['archive.file.transfer'].create({
            'file_id': self.file_01.id,
            'src_file_id': self.file_02.id
        })
        with self.assertRaises(ValidationError):
            self.file_01._transfer(transfer_2)

    def test_file_constrain_05(self):
        transfer = self.env['archive.file.transfer'].create({
            'file_id': self.file_01.id,
        })
        self.file_01._transfer(transfer)
        transfer_2 = self.env['archive.file.transfer'].create({
            'file_id': self.file_01.id,
            'src_location_id': self.location_01.id
        })
        with self.assertRaises(ValidationError):
            self.file_01._transfer(transfer_2)

    def test_onchange_document_transfer(self):
        transfer_wzd = self.env['archive.document.transfer.wizard'].new({
            'transfer_type': 'file',
            'dest_file_id': self.file_01.id
        })
        transfer_wzd.transfer_type = 'partner'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_file_id)
        transfer_wzd.dest_partner_id = self.archiving_partner
        transfer_wzd.transfer_type = 'file'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_partner_id)

    def test_onchange_file_transfer(self):
        transfer_wzd = self.env['archive.file.transfer.wizard'].new({
            'transfer_type': 'file',
            'dest_file_id': self.file_01.id
        })
        transfer_wzd.transfer_type = 'partner'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_file_id)
        transfer_wzd.dest_partner_id = self.archiving_partner
        transfer_wzd.transfer_type = 'location'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_partner_id)
        transfer_wzd.dest_location_id = self.location_01
        transfer_wzd.transfer_type = 'file'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_location_id)
