from .utilities import display_knowl

class SearchCol:
    def __init__(self, name, knowl, title, default=False, align="left", contingent=None, **kwds):
        self.name = name
        self.knowl = knowl
        self.title = title
        self.default = default
        self.orig = [name]
        self.height = 1
        self.contingent = contingent

        self.th_class = self.td_class = f"col-{name}"
        if align == "left":
            self.th_style = self.td_style = ""
        else:
            self.th_style = self.td_style = f"text-align:{align};"
        self.th_content = self.td_content = ""
        #print([k for k in kwds])

        for key, val in kwds.items():
            assert hasattr(self, key) and key.startswith("th_") or key.startswith("td_")
            setattr(self, key, getattr(self, key) + val)

    def get(self, rec):
        # We support dictionaries as well as classes like
        # AbvarFq_isoclass that are created in a postprocess step
        if isinstance(rec, dict):
            return rec.get(self.orig[0], "?")
        val = getattr(rec, self.name)
        if callable(val):
            return val()
        else:
            return val

    def display(self, rec):
        # default behavior is to just use the string representation of rec
        return str(self.get(rec))

    def display_knowl(self):
        if self.knowl:
            return display_knowl(self.knowl, self.title)
        else:
            return self.title

    def show(self, info, rank=None):
        if (self.contingent is None or self.contingent(info)) and (rank is None or rank == 0):
            yield self

class SpacerCol(SearchCol):
    def __init__(self, name, **kwds):
        super().__init__(name, None, None, **kwds)
        self.orig = []

    def display(self, rec):
        return ""

    def display_knowl(self):
        return ""

class MathCol(SearchCol):
    def __init__(self, name, knowl, title, default=False, align="center", orig=None, **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.orig = [orig if (orig is not None) else name]

    def display(self, rec):
        return f"${self.get(rec)}$"

class FloatCol(MathCol):
    def __init__(self, name, knowl, title, prec=3, default=False, align="center", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.prec = prec

    def get(self, rec):
        val = super().get(rec)
        # We mix string processing directives so that we can use variable precision
        return f"%.{self.prec}f" % val

class CheckCol(SearchCol):
    def __init__(self, name, knowl, title, default=False, align="center", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)

    def display(self, rec):
        return "&#x2713;" if self.get(rec) else ""

class LinkCol(SearchCol):
    def __init__(self, name, knowl, title, url_for, default=False, align="left", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.url_for = url_for

    def display(self, rec):
        return f'<a href="{self.url_for(self.get(rec))}">{self.get(rec)}</a>'

class ProcessedCol(SearchCol):
    def __init__(self, name, knowl, title, func, default=False, orig=None, mathmode=False, align="left", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.func = func
        self.orig = [orig if (orig is not None) else name]
        self.mathmode = mathmode

    def display(self, rec):
        s = self.func(self.get(rec))
        if s and self.mathmode:
            s = f"${s}$"
        return s

class ProcessedLinkCol(SearchCol):
    def __init__(self, name, knowl, title, url_func, disp_func, default=False, orig=None, align="left", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.url_func = url_func
        self.disp_func = disp_func
        self.orig = [orig if (orig is not None) else name]

    def display(self, rec):
        x = self.get(rec)
        url = self.url_func(x)
        disp = self.disp_func(x)
        return f'<a href="{url}">{disp}</a>'

class MultiProcessedCol(SearchCol):
    def __init__(self, name, knowl, title, inputs, func, default=False, mathmode=False, align="left", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.func = func
        self.orig = inputs
        self.mathmode = mathmode

    def display(self, rec):
        s = self.func(*[rec.get(col) for col in self.orig])
        if s != "" and self.mathmode:
            s = f"${s}$"
        return s

class ContingentCol(ProcessedCol):
    def __init__(self, name, knowl, title, func, contingent=lambda info:True, default=False, orig=None, mathmode=False, align="center", **kwds):
        super().__init__(name, knowl, title, func, default, orig, mathmode, align, **kwds)
        self.contingent = contingent

    def show(self, info, rank=None):
        if self.contingent(info) and (rank is None or rank == 0):
            yield self

class ColGroup(SearchCol):
    # See classical modular forms for an example
    def __init__(self, name, knowl, title, subcols, contingent=lambda info:True, default=False, orig=None, align="center", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.subcols = subcols
        self.contingent = contingent
        if orig is None:
            orig = sum([sub.orig for sub in subcols], [])
        self.orig = orig
        self.height = 2
        if not callable(subcols):
            self.th_content = f" colspan={len(subcols)}"

    def show(self, info, rank=None):
        if self.contingent(info):
            if callable(self.subcols):
                subcols = self.subcols(info)
                self.th_content = f" colspan={len(subcols)}"
            if rank == 0:
                yield self
            elif callable(self.subcols):
                yield from subcols
            else:
                yield from self.subcols

class SearchColumns:
    above_results = "" # Can add text above the Results (1-50 of ...) if desired
    above_table = "" # Can add text above the results table if desired
    dummy_download = False # change this to include dummy_download_search_results.html instead
    below_download = "" # Can add text above the bottom download links
    languages = None
    def __init__(self, columns, db_cols=None, tr_class=None):
        """
        INPUT:

        - ``columns`` -- a list of SearchCol objects
        """
        self.maxheight = maxheight = max(C.height for C in columns)
        if maxheight > 1:
            for C in columns:
                if C.height == 1:
                    # columns that have height > 1 are responsible for
                    # setting th_content on their own
                    C.th_content += fr" rowspan={maxheight}"
        self.columns = columns
        if db_cols is None:
            db_cols = sorted(set(sum([C.orig for C in columns], [])))
        self.db_cols = db_cols
        if tr_class is None:
            tr_class = ["" for _ in range(maxheight)]
        self.tr_class = tr_class

    def columns_shown(self, info, rank=None):
        # By default, this doesn't depend on info
        # rank is None in the body of the table, and 0..(maxrank-1) in the header
        for C in self.columns:
            yield from C.show(info, rank)