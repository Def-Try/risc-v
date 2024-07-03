import pstats

class Stats(pstats.Stats):
    # list the tuple indices and directions for sorting,
    # along with some printable description
    sort_arg_dict_default = {
      "calls"            : (((1,-1),              ), "call count"),
      "ncalls"           : (((1,-1),              ), "call count"),
      "cumtime"          : (((4,-1),              ), "cumulative time"),
      "cumulative"       : (((4,-1),              ), "cumulative time"),
      "file"             : (((6, 1),              ), "file name"),
      "filename"         : (((6, 1),              ), "file name"),
      "line"             : (((7, 1),              ), "line number"),
      "module"           : (((6, 1),              ), "file name"),
      "name"             : (((8, 1),              ), "function name"),
      "nfl"              : (((8, 1),(6, 1),(7, 1),), "name/file/line"),
      "pcalls"           : (((0,-1),              ), "primitive call count"),
      "stdname"          : (((9, 1),              ), "standard name"),
      "time"             : (((2,-1),              ), "internal time"),
      "tottime"          : (((2,-1),              ), "internal time"),
      "cumulativepercall": (((5,-1),              ), "cumulative time per call"),
      "totalpercall"     : (((3,-1),              ), "total time per call"),
      }


    def sort_stats(self, *field):
      if not field:
        self.fcn_list = 0
        return self
      if len(field) == 1 and isinstance(field[0], int):
        # Be compatible with old profiler
        field = [ {-1: "stdname",
                    0:  "calls",
                    1:  "time",
                    2:  "cumulative"}[field[0]] ]
      elif len(field) >= 2:
        for arg in field[1:]:
          if type(arg) != type(field[0]):
            raise TypeError("Can't have mixed argument type")

      sort_arg_defs = self.get_sort_arg_defs()

      sort_tuple = ()
      self.sort_type = ""
      connector = ""
      for word in field:
        if isinstance(word, pstats.SortKey):
          word = word.value
        sort_tuple = sort_tuple + sort_arg_defs[word][0]
        self.sort_type += connector + sort_arg_defs[word][1]
        connector = ", "
  
      stats_list = []
      for func, (cc, nc, tt, ct, callers) in self.stats.items():
        if nc == 0:
          npc = 0
        else:
          npc = float(tt)/nc

        if cc == 0:
          cpc = 0
        else:
          cpc = float(ct)/cc

        stats_list.append((cc, nc, tt, npc, ct, cpc) + func +
                          (pstats.func_std_string(func), func))

      stats_list.sort(key=pstats.cmp_to_key(pstats.TupleComp(sort_tuple).compare))

      self.fcn_list = fcn_list = []
      for tuple in stats_list:
        fcn_list.append(tuple[-1])
      return self

s = Stats('profile.log')
s.sort_stats('cumulativepercall')
s.print_stats()