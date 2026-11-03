"""Task 8: screenshot real game screens with the built mod installed (isolated env).
python -E -m tools.visual_check <version>"""
import sys
from tools.build import build
from tools.harness import ENV, run
from tools.paths import DIST

LABEL_SHOTS = [
    ('menu-settings', ['gui-menu.single-player-menu', 'gui-menu.multi-player', 'gui-menu.settings', 'gui.exit',
                       'gui-interface-settings.alt-mode', 'gui-control-settings.controller-icons-auto',
                       'gui-map-generator.title']),
    ('items-tooltips', ['item-name.iron-plate', 'item-description.speed-module', 'entity-name.assembling-machine-2',
                        'entity-description.recycler', 'entity-name.bulk-inserter',
                        'entity-description.item-on-ground', 'entity-description.heating-tower']),
    ('technology', ['technology-name.automation', 'technology-description.automation',
                    'technology-name.advanced-circuit', 'technology-description.advanced-circuit']),
    ('tips', ['tips-and-tricks-item-name.fast-replace', 'tips-and-tricks-item-description.active-provider-chest',
              'tips-and-tricks-item-description.belt-lanes']),
    ('space-age', ['space-location-name.vulcanus', 'space-location-description.vulcanus',
                   'space-location-name.fulgora', 'space-location-name.gleba', 'space-location-name.aquilo',
                   'entity-name.foundry', 'entity-description.foundry', 'quality-name.legendary']),
    ('controls', ['controls.build', 'controls.rotate', 'controls.pick-items', 'controls.open-character-gui',
                  'controls.toggle-map']),
    ('scenario', ['msg-intro']),
]
GUI_SHOTS = ['production', 'bonus', 'achievement', 'trains']


def shots():
    out = [{'name': n, 'title': f'FA {n}', 'rows': [[k] for k in keys]} for n, keys in LABEL_SHOTS]
    return out + [{'name': g, 'gui_type': g} for g in GUI_SHOTS]


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    mod = build(sys.argv[1], out_root=DIST)
    for p in run(shots(), '', extra_mods=[mod], tag=f'phase3-{sys.argv[1]}', timeout=420):
        print(p)
