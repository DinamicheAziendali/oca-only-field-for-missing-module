from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    openupgrade.load_data(
        env.cr,
        "l10n_it_riba_oca",
        "migrations/18.0.1.10.2/noupdate.xml",
    )

    openupgrade.map_values(
        cr,
        openupgrade.get_legacy_name("state"),
        "state",
        [
            ("draft", "draft"),
            ("confirmed", "confirmed"),
            ("accredited", "credited"),
            ("paid", "paid"),
            ("unsolved", "past_due"),
            ("cancel", "cancel"),
        ],
        table="riba_slip_line",
    )

    openupgrade.map_values(
        cr,
        openupgrade.get_legacy_name("state"),
        "state",
        [
            ("draft", "draft"),
            ("accepted", "accepted"),
            ("accredited", "credited"),
            ("paid", "paid"),
            ("unsolved", "past_due"),
            ("cancel", "cancel"),
        ],
        table="riba_slip",
    )
