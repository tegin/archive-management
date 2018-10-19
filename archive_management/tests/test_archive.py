from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestArchiveManagementSystem(TransactionCase):
    def setUp(self):
        super().setUp()
        self.repo = self.env['archive.repository'].create({
            'name': 'Repo',
            'model_ids': [(4, self.browse_ref('base.model_res_partner').id)],
            'level_max_difference': 2,
        })
        self.level_01 = self.env['archive.repository.level'].create({
            'name': 'Subseries',
            'level': 1,
            'can_assign_files': True,
            'repository_id': self.repo.id,
        })
        self.level_02 = self.env['archive.repository.level'].create({
            'name': 'Series',
            'level': 2,
            'repository_id': self.repo.id,
        })
        self.level_03 = self.env['archive.repository.level'].create({
            'name': 'Box',
            'level': 3,
            'repository_id': self.repo.id,
        })
        self.location_01 = self.env['archive.location'].create({
            'description': 'LOC1'
        })
        self.location_02 = self.env['archive.location'].create({
            'description': 'LOC2'
        })
        self.storage_01 = self.env['archive.storage'].create({
            'repository_level_id': self.level_01.id,
        })
        self.storage_02 = self.env['archive.storage'].create({
            'repository_level_id': self.level_01.id,
        })
        self.storage_03 = self.env['archive.storage'].create({
            'repository_level_id': self.level_01.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner'
        })
        self.archiving_partner = self.env['res.partner'].create({
            'name': 'Archiving user',
        })

    def new_file(self, partner=False):
        if not partner:
            partner = self.partner
        action = self.env['archive.file.add'].new({
            'repository_id': self.repo.id,
            'model': partner._name,
            'res_id': partner.id
        })
        self.assertIn(self.repo, action.repository_ids)
        action = action.create(action._convert_to_write(action._cache))
        doc = self.env['archive.file'].browse(action.run()['res_id'])
        self.assertEqual(doc.res, partner)
        return doc

    def test_file_moves(self):
        file = self.new_file()
        self.assertFalse(file.storage_id)
        self.assertFalse(file.partner_id)
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'storage',
            'file_id': file.id,
            'dest_storage_id': self.storage_01.id,
        }).run()
        self.assertEqual(file.storage_id, self.storage_01)
        self.assertFalse(file.partner_id)
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'partner',
            'file_id': file.id,
            'dest_partner_id': self.archiving_partner.id,
        }).run()
        self.assertFalse(file.storage_id)
        self.assertEqual(file.partner_id, self.archiving_partner)

    def test_file_destruction(self):
        file = self.new_file()
        self.env['archive.file.transfer.wizard'].create({
            'transfer_type': 'storage',
            'file_id': file.id,
            'dest_storage_id': self.storage_01.id,
        }).run()
        self.storage_01.destroy()
        self.assertTrue(file.destruction_date)

    def test_destruction(self):
        self.assertTrue(self.storage_01.active)
        self.assertTrue(self.storage_02.active)
        self.assertTrue(self.storage_03.active)
        self.env['archive.storage.transfer.wizard'].create({
            'transfer_type': 'storage',
            'storage_id': self.storage_02.id,
            'dest_storage_id': self.storage_03.id,
        }).run()
        self.env['archive.storage.transfer.wizard'].create({
            'transfer_type': 'storage',
            'storage_id': self.storage_01.id,
            'dest_storage_id': self.storage_02.id,
        }).run()
        self.storage_02.destroy()
        self.assertFalse(self.storage_02.active)
        self.assertFalse(self.storage_01.active)
        self.assertTrue(self.storage_03.active)

    def test_move(self):
        self.assertTrue(self.storage_01.parent_ids)
        self.assertFalse(self.storage_01.storage_id)
        self.assertFalse(self.storage_01.location_id)
        self.assertFalse(self.storage_01.partner_id)
        self.env['archive.storage.transfer.wizard'].create({
            'transfer_type': 'storage',
            'storage_id': self.storage_01.id,
            'dest_storage_id': self.storage_02.id,
        }).run()
        self.assertEqual(self.storage_01.storage_id, self.storage_02)
        self.assertFalse(self.storage_01.location_id)
        self.assertFalse(self.storage_01.partner_id)
        self.assertFalse(self.storage_01.current_location_id)
        self.env['archive.storage.transfer.wizard'].create({
            'transfer_type': 'storage',
            'storage_id': self.storage_02.id,
            'dest_location_id': self.location_01.id,
        }).run()
        self.assertEqual(self.storage_01.current_location_id, self.location_01)
        self.assertFalse(self.storage_01.location_id)
        self.assertFalse(self.storage_01.partner_id)
        self.assertEqual(self.storage_02.current_location_id, self.location_01)
        self.assertEqual(self.storage_02.location_id, self.location_01)
        self.env['archive.storage.transfer.wizard'].create({
            'transfer_type': 'storage',
            'storage_id': self.storage_01.id,
            'dest_location_id': self.location_02.id,
        }).run()
        self.assertFalse(self.storage_01.storage_id)
        self.assertFalse(self.storage_01.partner_id)
        self.assertEqual(self.storage_01.location_id, self.location_02)
        self.assertEqual(self.storage_01.current_location_id, self.location_02)
        self.env['archive.storage.transfer.wizard'].create({
            'transfer_type': 'storage',
            'storage_id': self.storage_01.id,
            'dest_partner_id': self.archiving_partner.id,
        }).run()
        self.assertFalse(self.storage_01.storage_id)
        self.assertEqual(self.storage_01.partner_id, self.archiving_partner)
        self.assertFalse(self.storage_01.location_id)

    def test_repository_constrains(self):
        self.assertTrue(self.repo.active)
        with self.assertRaises(ValidationError):
            self.repo.toggle_active()
        self.storage_01.destroy()
        self.storage_02.destroy()
        self.storage_03.destroy()
        self.repo.toggle_active()
        self.assertFalse(self.repo.active)

    def test_recursion(self):
        storage = self.storage_01
        new_storage = self.env['archive.storage'].create({
            'repository_level_id': self.level_01.id,
        })
        for i in range(1, 10):
            wizard = self.env['archive.storage.transfer.wizard'].create({
                'transfer_type': 'storage',
                'storage_id': storage.id,
                'dest_storage_id': new_storage.id,
            })
            self.assertEqual(wizard.min_level, 2)
            self.assertEqual(wizard.max_level, 3)
            wizard.run()
            storage = new_storage
            new_storage = self.env['archive.storage'].create({
                'repository_level_id': self.level_01.id,
            })
        with self.assertRaises(ValidationError):
            self.env['archive.storage.transfer.wizard'].create({
                'transfer_type': 'storage',
                'storage_id': storage.id,
                'dest_storage_id': self.storage_01.id,
            }).run()

    def test_file_constrain_01(self):
        file = self.new_file()
        file_2 = self.new_file(partner=self.archiving_partner)
        transfer = self.env['archive.file.transfer'].create({
            'file_id': file_2.id,
        })
        with self.assertRaises(ValidationError):
            file._transfer(transfer)

    def test_file_constrain_02(self):
        file = self.new_file()
        file_2 = self.new_file(partner=self.archiving_partner)
        transfer = self.env['archive.file.transfer'].create({
            'file_id': file_2.id,
        })
        with self.assertRaises(ValidationError):
            file.parent_id.write({'transfer_id': transfer.id})

    def test_file_constrain_03(self):
        file = self.new_file()
        transfer = self.env['archive.file.transfer'].create({
            'file_id': file.id,
        })
        file._transfer(transfer)
        transfer_2 = self.env['archive.file.transfer'].create({
            'file_id': file.id,
            'src_storage_id': self.storage_01.id
        })
        with self.assertRaises(ValidationError):
            file._transfer(transfer_2)

    def test_file_constrain_04(self):
        file = self.new_file()
        transfer = self.env['archive.file.transfer'].create({
            'file_id': file.id,
        })
        file._transfer(transfer)
        transfer_2 = self.env['archive.file.transfer'].create({
            'file_id': file.id,
            'src_partner_id': self.partner.id
        })
        with self.assertRaises(ValidationError):
            file._transfer(transfer_2)

    def test_storage_constrain_01(self):
        transfer = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_02.id,
        })
        with self.assertRaises(ValidationError):
            self.storage_01.parent_id.write({'transfer_id': transfer.id})

    def test_storage_constrain_02(self):
        transfer = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_02.id,
        })
        with self.assertRaises(ValidationError):
            self.storage_01._transfer(transfer)

    def test_storage_constrain_03(self):
        transfer = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_01.id,
        })
        self.storage_01._transfer(transfer)
        transfer_2 = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_01.id,
            'src_partner_id': self.partner.id
        })
        with self.assertRaises(ValidationError):
            self.storage_01._transfer(transfer_2)

    def test_storage_constrain_04(self):
        transfer = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_01.id,
        })
        self.storage_01._transfer(transfer)
        transfer_2 = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_01.id,
            'src_storage_id': self.storage_02.id
        })
        with self.assertRaises(ValidationError):
            self.storage_01._transfer(transfer_2)

    def test_storage_constrain_05(self):
        transfer = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_01.id,
        })
        self.storage_01._transfer(transfer)
        transfer_2 = self.env['archive.storage.transfer'].create({
            'storage_id': self.storage_01.id,
            'src_location_id': self.location_01.id
        })
        with self.assertRaises(ValidationError):
            self.storage_01._transfer(transfer_2)

    def test_onchange_file_transfer(self):
        transfer_wzd = self.env['archive.file.transfer.wizard'].new({
            'transfer_type': 'storage',
            'dest_storage_id': self.storage_01.id
        })
        transfer_wzd.transfer_type = 'partner'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_storage_id)
        transfer_wzd.dest_partner_id = self.archiving_partner
        transfer_wzd.transfer_type = 'storage'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_partner_id)

    def test_onchange_storage_transfer(self):
        transfer_wzd = self.env['archive.storage.transfer.wizard'].new({
            'transfer_type': 'storage',
            'dest_storage_id': self.storage_01.id
        })
        transfer_wzd.transfer_type = 'partner'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_storage_id)
        transfer_wzd.dest_partner_id = self.archiving_partner
        transfer_wzd.transfer_type = 'location'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_partner_id)
        transfer_wzd.dest_location_id = self.location_01
        transfer_wzd.transfer_type = 'storage'
        transfer_wzd._onchange_transfer_type()
        self.assertFalse(transfer_wzd.dest_location_id)
