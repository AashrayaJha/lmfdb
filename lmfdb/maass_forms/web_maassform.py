# -*- coding: utf-8 -*-

from lmfdb import db
from lmfdb.utils import display_knowl, Downloader
from lmfdb.backend.encoding import Json
from flask import url_for, abort
from sage.all import ZZ

def th_wrap(kwl, title):
    return '    <th>%s</th>' % display_knowl(kwl, title=title)
def td_wrapl(val):
    return '    <td align="left">%s</td>' % val
def td_wrapc(val):
    return '    <td align="center">%s</td>' % val
def td_wrapr(val):
    return '    <td align="right">%s</td>' % val

def parity_text(val):
    return 'odd' if val == -1 else 'even'

class WebMaassForm(object):
    def __init__(self, data):
        self.__dict__.update(data)
        self._data = data

    @staticmethod
    def by_label(label):
        try:
            data = db.maass_newforms.lookup(label)
        except AttributeError:
            raise KeyError("Maass newform %s not found in database."%(label))
        return WebMaassForm(data)

    @staticmethod
    def by_maass_id(maass_id):
        return self.by_label(maass_id)

    @property
    def label(self):
        return self.maass_id #TODO: we should revisit this at some point

    @property
    def next_maass_form(self):
        # return the "next" maass form of the save level, character, and weight with spectral parameter approximately >= our spectral _parameter
        # forms with the same spectral parameter are sorted by maass_id
        query = {'level':self.level,  'weight': self.weight, 'conrey_index':self.conrey_index, 'spectral_parameter': self.spectral_parameter, 'maass_id': {'$gt':self.maass_id}}
        forms = db.maass_newforms.esearch(query, sort=["maass_id"], projection='maass_id', limit=1)
        if forms:
            return forms[0];
        query = {'level':self.level,  'weight': self.weight, 'conrey_index':self.conrey_index, 'spectral_parameter': {'$gt': self.spectral_parameter}}
        forms = db.maass_forms.search(query, sort=["spectral_parameter","maass_id"], projection='maass_id', limit=1)
        return forms[0] if forms else None

    def prev_maass_form(self, level, character, weight, eigenvalue, maass_id):
        query = {'level':self.level,  'weight': self.weight, 'conrey_index':self.conrey_index, 'spectral_parameter': self.spectral_parameter, 'maass_id': {'$lt':self.maass_id}}
        forms = db.maass_newforms.esearch(query, sort=["maass_id"], projection='maass_id', limit=1)
        if forms:
            return forms[0];
        query = {'level':self.level,  'weight': self.weight, 'conrey_index':self.conrey_index, 'spectral_parameter': {'$lt': self.spectral_parameter}}
        forms = db.maass_forms.search(query, sort=["spectral_parameter","maass_id"], projection='maass_id', limit=1)
        return forms[0] if forms else None

    @property
    def title(self):
        return r"Maass form on \(\Gamma_0(%d)\) with \(R=%s\)"%(self.level,self.spectral_parameter)

    @property
    def properties(self):
        return [('Level', str(self.level)),
                ('Weight', str(self.weight)),
                ('Character', self.character_label),
                ('Symmetry', self.symmetry_pretty),
                ]

    @property
    def factored_level(self):
        return ' = ' + ZZ(self.level).factor()._latex_()

    @property
    def character_label(self):
        return "%d.%d"%(self.level, self.conrey_index)

    @property
    def character_link(self):
        return display_knowl('character.dirichlet.data', title=self.character_label, kwargs={'label':self.character_label})

    @property
    def symmetry_pretty(self):
        return "even" if self.symmetry == 1 else ("odd" if self.symmetry == -1 else "")

    @property
    def fricke_eigenvalue_pretty(self):
        return "%+d"%(self.fricke_eigenvalue) if (self.conrey_index == 1 and self.fricke_eigenvalue) else ""

    @property
    def bread(self):
        return [('Modular forms', url_for('modular_forms')),
                ('Maass', url_for(".index")),
                ("Level %d"%(self.level), url_for(".by_level",level=self.level)),
                ("Weight %d"%(self.weight), url_for(".by_level_weight",level=self.level,weight=self.weight)),
                ("Character %s"%(self.character_label), url_for(".by_level_weight_character",weight=self.weight,level=self.level,conrey_index=self.conrey_index)),
                ]

    @property
    def downloads(self):
        return [("Coefficients to text", url_for (".download_coefficients", label=self.label)),
                ("All stored data to text", url_for (".download", label=self.label)),
                ]

    @property
    def friends(self):
        return [("L-function", "/L" + url_for(".by_label",label=self.label))]

    def coefficient_table(self, rows=20, cols=5):
        if not self.coefficients:
            return ""
        n = len(self.coefficients)
        assert rows > 0 and cols > 0
        table = ['<table class="ntdata"><tr><th></th></tr>']
        if (rows-1)*cols >= n:
            rows = (n // cols) + (1 if (n%cols) else 0)
        for i in range(rows):
            table.append('<tr>')
            for j in range(cols):
                if i*cols+j > n:
                    break
                table.append(td_wrapr(r"\(a_{%d}=%+.9f\)"%(i*cols+j+1,self.coefficients[i*cols+j])))
            table.append('</tr>')
        table.append('</table>')
        if rows*cols < n:
            table.append('<p>Showing %d of %d available coefficients</p>' % (rows*cols,n))
        return '\n'.join(table)


class MaassFormDownloader(Downloader):

    def download(self, label, lang='text'):
        data = db.maass_newforms.lookup(label)
        if data is None:
            return abort(404, "Maass form %s not found in the database"%label)
        for col in db.maass_newforms.col_type:
            if db.maass_newforms.col_type[col] == "numeric" and data.get(col):
                data[col] = str(data[col])
            if db.maass_newforms.col_type[col] == "numeric[]" and data.get(col):
                data[col] = [str(data[col][n]) for n in range(len(data[col]))]
        return self._wrap(Json.dumps(data),
                          label,
                          lang=lang,
                          title='All stored data for Maass form %s,'%(label))

    def download_coefficients(self, label, lang='text'):
        data = db.maass_newforms.lookup(label, projection="coefficients")
        if data is None:
            return abort(404, "Coefficient data for Maass form %s not found in the database"%label)
        c = data
        data = [str(c[n]) for n in range(len(c))]
        return self._wrap(Json.dumps(data).replace('"',''),
                          label + '.coefficients',
                          lang=lang,
                          title='Coefficients for Maass form %s,'%(label))
