"""Comparison figures: two-panel flood/PIM maps and the Abzucht HQ100 overview.

make_map is ported from bin/analysis/compare_goslar_multiriver.py (the sparse x-tick
variant replaces the plt.subplots patch in report_goslar_multiriver_full.py);
hq100_figure is the figure block of bin/analysis/compare_abzucht_hq100.py.
"""

from __future__ import annotations

import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

LABELS = {'flood_hazard': 'Flood indicators', 'sediment': 'Erosion factors', 'landuse_asm': 'Land cover',
          'environmental': 'Water / ecology', 'socioeconomic': 'Access / exposure'}
COLORS = ['#ffffcc', '#ffeda0', '#feb24c', '#f03b20', '#bd0026']
CLASS_BOUNDS = [0, .2, .4, .6, .8, 1.000001]


def _extent_km(profile):
    t = profile['transform']
    return [t.c / 1000, (t.c + t.a * profile['width']) / 1000, (t.f + t.e * profile['height']) / 1000, t.f / 1000]


def make_map(path, title, products, limits, flood, pim, ref, sparse_x_ticks=False):
    """Flood indicator (left) and PIM (right) with official flood-zone outlines; PNG and SVG."""
    import geopandas as gpd
    extent = _extent_km(ref)
    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    if sparse_x_ticks:
        # Narrow river extents need explicit tick density after the equal-aspect layout.
        for ax in np.asarray(axes).flat:
            ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
    fig.subplots_adjust(left=.075, right=.965, top=.87, bottom=.17, wspace=.22)
    cmap = ListedColormap(COLORS)
    cmap.set_bad('#f0f0f0')
    norm = BoundaryNorm(CLASS_BOUNDS, 5)
    for ax, array, label in zip(axes, [flood, pim], ['Flood-conditioning indicator', 'Composite priority (PIM)']):
        im = ax.imshow(np.ma.masked_invalid(array), extent=extent, origin='upper', cmap=cmap, norm=norm,
                       interpolation='nearest')
        for p in products:
            gs = gpd.GeoSeries([p['geometry']], crs=ref['crs']).scale(.001, .001, origin=(0, 0))
            gs.boundary.plot(ax=ax, color='#005da8', linewidth=.8)
        ax.set_facecolor('#f0f0f0')
        ax.set_xlim(limits[0] / 1000, limits[2] / 1000)
        ax.set_ylim(limits[1] / 1000, limits[3] / 1000)
        ax.set_aspect('equal')
        ax.set_title(label, fontsize=12, loc='left')
        ax.set_xlabel('UTM easting (km)')
        ax.set_ylabel('UTM northing (km)')
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.tick_params(labelsize=8)
        # Scale bar: the largest round length below a quarter of the panel width.
        span = (limits[2] - limits[0]) / 1000
        length = next((v for v in [5, 2, 1, .5, .2, .1] if v < span / 4), .05)
        x = limits[0] / 1000 + .06 * span
        y = limits[1] / 1000 + .06 * (limits[3] - limits[1]) / 1000
        ax.plot([x, x + length], [y, y], color='black', linewidth=2)
        ax.text(x + length / 2, y, f'{length:g} km', ha='center', va='bottom', fontsize=8,
                bbox=dict(facecolor='white', edgecolor='none', alpha=.8, pad=1))
    fig.suptitle(title, fontsize=19, y=.965)
    cb = fig.add_axes([.33, .10, .36, .024])
    fig.colorbar(im, cax=cb, orientation='horizontal', ticks=[0, .2, .4, .6, .8, 1])
    fig.legend(handles=[Line2D([0], [0], color='#005da8', label='Official flood-zone boundary'),
                        Patch(facecolor='#f0f0f0', label='No model score')],
               loc='lower center', bbox_to_anchor=(.51, .012), ncol=2, frameon=False, fontsize=10)
    for fmt in ['png', 'svg']:
        fig.savefig(path.with_suffix('.' + fmt), dpi=180)
    plt.close(fig)


def hq100_figure(out, pim, profile, vectors, boundary, geom, categories, stats, means, weights,
                 coverage_fraction):
    """Abzucht HQ100 overview: PIM map, coverage categories, class shares and contributions."""
    fig = plt.figure(figsize=(16, 9), facecolor='white')
    gs = fig.add_gridspec(2, 3, height_ratios=[3.4, 1.3], left=.14, right=.97, top=.85, bottom=.20,
                          wspace=.65, hspace=.48)
    ax1 = fig.add_subplot(gs[0, :2])
    ax2 = fig.add_subplot(gs[0, 2])
    ax3 = fig.add_subplot(gs[1, :2])
    ax4 = fig.add_subplot(gs[1, 2])
    extent = _extent_km(profile)
    plotvec = vectors.copy()
    plotvec.geometry = plotvec.geometry.scale(xfact=.001, yfact=.001, origin=(0, 0))
    plotbound = boundary.copy()
    plotbound.geometry = plotbound.geometry.scale(xfact=.001, yfact=.001, origin=(0, 0))
    xmin, ymin, xmax, ymax = geom.bounds
    for ax in [ax1, ax2]:
        ax.set_facecolor('#eef0f3')
        ax.set_xlim(xmin / 1000 - .5, xmax / 1000 + .5)
        ax.set_ylim(ymin / 1000 - .5, ymax / 1000 + .5)
        ax.set_aspect('equal')
        ax.tick_params(labelsize=8)
        ax.set_xlabel('UTM easting (km)', fontsize=9)
    ax1.imshow(np.ma.masked_invalid(pim), extent=extent, origin='upper', cmap=ListedColormap(COLORS),
               norm=BoundaryNorm(CLASS_BOUNDS, 5), interpolation='nearest')
    plotvec.boundary.plot(ax=ax1, color='#0656a0', linewidth=1.3)
    plotbound.boundary.plot(ax=ax1, color='#444444', linewidth=.7, linestyle='--')
    ax1.set_ylabel('UTM northing (km)', fontsize=9)
    ax1.set_title('Goslar / Abzucht: official HQ100 outline over current priority', loc='left', fontsize=12)
    ax1.legend(handles=[Line2D([0], [0], color='#0656a0', label='Official HQ100'),
                        Line2D([0], [0], color='#444444', ls='--', label='Project boundary'),
                        Patch(color='#eef0f3', label='No PIM data')], loc='lower right', fontsize=8)
    ax2.imshow(np.ma.masked_where(categories == 0, categories), extent=extent, origin='upper',
               cmap=ListedColormap(['#8d96a4', '#eac36b', '#d54436']), norm=BoundaryNorm([.5, 1.5, 2.5, 3.5], 3),
               interpolation='nearest')
    plotvec.boundary.plot(ax=ax2, color='#0656a0', linewidth=.5)
    ax2.set_title('Coverage inside HQ100', loc='left', fontsize=12)
    ax2.legend(handles=[Patch(color=c, label=l) for c, l in
                        [('#8d96a4', 'No PIM data'), ('#eac36b', 'PIM < 0.6'), ('#d54436', 'PIM >= 0.6')]],
               loc='lower right', fontsize=8)
    class_names = ['0-.2', '.2-.4', '.4-.6', '.6-.8', '.8-1']
    bottom = np.zeros(3)
    for k, color in enumerate(COLORS):
        widths = np.array([100 * s['class_counts'][k] / s['valid_cells'] for s in stats.values()])
        ax3.barh(np.arange(3), widths, left=bottom, color=color, label=class_names[k], edgecolor='white')
        bottom += widths
    ax3.set_yticks(range(3), ['Inside HQ100', 'Outside, within 1 km', 'Full valid project'])
    ax3.invert_yaxis()
    ax3.set_xlim(0, 100)
    ax3.set_xlabel('Share of valid pixels (%)', fontsize=10)
    ax3.set_title('Priority distribution (NoData excluded)', loc='left', fontsize=12)
    ax3.legend(ncol=5, fontsize=8, loc='upper center', bbox_to_anchor=(.5, -.38), frameon=False, title='PIM score')
    a = np.array(list(means.values()))
    y = np.arange(5)
    ax4.barh(y - .17, a[:, 0], height=.32, color='#0656a0', label='HQ100')
    ax4.barh(y + .17, a[:, 1], height=.32, color='#a6b7c9', label='1 km ring')
    ax4.set_yticks(y, [LABELS[k] for k in weights], fontsize=8)
    ax4.invert_yaxis()
    ax4.set_xlabel('Mean weighted contribution', fontsize=9)
    ax4.set_title('What contributes to the score?', loc='left', fontsize=11)
    ax4.legend(fontsize=8, loc='lower right')
    si = stats['HQ100 polygon']
    sr = stats['Outside polygon, within 1 km']
    fig.suptitle(f"Covered HQ100 area: mean priority {si['mean']:.2f} versus {sr['mean']:.2f} nearby",
                 x=.045, ha='left', fontsize=21, fontweight='bold', y=.97)
    subtitle = (f'{100 * coverage_fraction:.0f}% of the official polygon lies inside the project boundary. '
                'Grey areas have no PIM result.' if coverage_fraction < .999 else
                'The full official polygon is now covered. Composite scores can still contain gaps in underlying inputs.')
    fig.text(.045, .91, subtitle, fontsize=12)
    fig.text(.045, .025, 'Prototype scenario comparison | NLWKN HQ100 (2026; local snapshot) | '
             'Existing 30 m PIM and weights | Not observed-event accuracy', fontsize=10, color='#444444')
    for fmt in ['png', 'svg']:
        fig.savefig(out / f'abzucht_hq100_comparison.{fmt}', dpi=180)
    plt.close(fig)
