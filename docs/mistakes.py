
                method = self.s.recv(4)
                self.s.unrecv(method)
                print("xxx unrecv'd [{}]".format(method))

                # jython used to do this, they stopped since it's broken
                # but reimplementing sendall is out of scope for now
                if not getattr(self.s.s, "sendall", None):
                    self.s.s.sendall = self.s.s.send

                # TODO this is also pretty bad
                have = dir(self.s)
                for k in self.s.s.__dict__:
                    if k not in have and not k.startswith("__"):
                        if k == "recv":
                            raise Exception("wait what")

                        self.s.__dict__[k] = self.s.s.__dict__[k]

                have = dir(self.s)
                for k in dir(self.s.s):
                    if k not in have and not k.startswith("__"):
                        if k == "recv":
                            raise Exception("wait what")

                        setattr(self.s, k, getattr(self.s.s, k))
