### hello world

* qwe
* asd
  * zxc
  * 573
    * one
    * two
    
  * |||
    |--|--|
    |listed|table|

```
[72....................................................................]
[80............................................................................]
```

* foo
  ```
  [72....................................................................]
  [80............................................................................]
  ```

  * bar
    ```
    [72....................................................................]
    [80............................................................................]
    ```

```
l[i]=1I;(){}o0O</> var foo = "$(`bar`)"; a's'd
```

🔍🌽.📕.🍙🔎

[](#s1)
[s1](#s1)
[#s1](#s1)

a123456789b123456789c123456789d123456789e123456789f123456789g123456789h123456789i123456789j123456789k123456789l123456789m123456789n123456789o123456789p123456789q123456789r123456789s123456789t123456789u123456789v123456789w123456789x123456789y123456789z123456789

<foo> &nbsp; bar &amp; <span>baz</span>
<a href="?foo=bar&baz=qwe&amp;rty">?foo=bar&baz=qwe&amp;rty</a>
<!-- hidden -->
```
<foo> &nbsp; bar &amp; <span>baz</span>
<a href="?foo=bar&baz=qwe&amp;rty">?foo=bar&baz=qwe&amp;rty</a>
<!-- visible -->
```

*fails marked/showdown/tui/simplemde (just italics), **OK: markdown-it/simplemde:***  
testing just google.com and underscored _google.com_ also with _google.com,_ trailing comma and _google.com_, comma after

*fails tui (just italics), **OK: marked/showdown/markdown-it/simplemde:***  
testing just https://google.com and underscored _https://google.com_ links like that

*fails marked (no markup) and showdown/tui/simplemde (no links at all), **OK: markdown-it:***  
let's try <google.com> bracketed and _<google.com>_ underscored bracketed

*fails marked (literal underscore), **OK: showdown/markdown-it/simplemde:***  
let's try <https://google.com> bracketed and _<https://google.com>_ underscored bracketed

*fails none:*  
and then [google](google.com) verbose and _[google](google.com)_ underscored  

*fails none:*  
and then [google](https://google.com/) verbose and _[google](https://google.com/)_ underscored

*all behave similarly (only verbose ones):*  
and then <local> or maybe <./local> fsgfds </absolute> fsgfds  
and then [local] or maybe [./local] fsgfds [/absolute] fsgfds  
and then (local) or maybe (./local) fsgfds (/absolute) fsgfds  
and then [](local) or maybe [](./local) fsgfds [](/absolute) fsgfds  
and then [.](local) or maybe [.](./local) fsgfds [.](/absolute) fsgfds  
and then [asdf](local) or maybe [asdf](./local) fsgfds [asdf](/absolute) fsgfds

*`ng/OK/OK/OK markdown-it`  
`ng/OK/ng/OK marked`  
`ng/OK/OK/OK showdown`
`OK/OK/OK/OK simplemde`*  
[with spaces](/with spaces) plain, [with spaces](/with%20spaces) %20, [with spaces](</with spaces>) brackets, [with spaces](/with%20spaces) %20

*this fails marked, **OK: markdown-it, simplemde:***

* testing a list with:
  `some code after a newline`

* testing a list with:
  just a newline

and here is really just
a newline toplevel

*this fails showdown/hypermd, **OK: marked/markdown-it/simplemde:***

* testing a list with

      code here
      and a newline
        this should have two leading spaces

  * second list level

        more code here
        and a newline
          this should have two leading spaces

.

* testing a list with

      code here
      and a newline
        this should have two leading spaces

    * second list level

          more code here
          and a newline
            this should have two leading spaces

*this fails stackedit, **OK: showdown/marked/markdown-it/simplemde:***

|||
|--|--|
| a table | with no header |
| second row | foo bar |

*this fails showdown/stackedit, **OK: marked/markdown-it/simplemde:***

|||
|--|--:|
| a table | on the right |
| second row | foo bar |

||
--|:-:|-:
a table | big text in this | aaakbfddd
second row | centred | bbb

||
--|--|--
foo

* list entry
* [x] yes
* [ ] no
* another entry

# s1
## ep1
## ep2
# s2
## ep1
## ep2
# s3
## ep1
## ep2



#######################################################################



marked:
  works in last ff/chrome for xp
  bug: config{breaks:true} does nothing in 1.0
  use whitespace, no tabs

showdown:
  ie6 and ie8 broken, works in last ff/chrome for xp

markdown-it:
  works in last ff/chrome for xp
  use whitespace, no tabs
  no header anchors

tui wysiwyg:
  requires links to be <http://> or [title](location)



links:
  http://demo.showdownjs.com/
  https://marked.js.org/demo/
  https://markdown-it.github.io/
  https://simplemde.com/



all-pass:

https://github.com/joemccann/dillinger
  https://dillinger.io/
  uses markdown-it

https://github.com/markdown-it/markdown-it
  https://markdown-it.github.io/



almost-all-pass:

https://github.com/Ionaru/easy-markdown-editor
  https://easymde.tk/
  simplemde fork (the most active)

https://github.com/Inscryb/inscryb-markdown-editor
  simplemde fork

other simplemde forks:
  pulkitmittal

https://simplemde.com/
  (dead)

https://github.com/nhn/tui.editor
  https://nhn.github.io/tui.editor/latest/tutorial-example01-editor-basic
  ie10 and up



unrelated neat stuff:
  https://github.com/gnab/remark



```sh
awk '/./ {printf "%s %d\n", $0, NR; next} 1' <test.md >ln.md
gawk '{print gensub(/([a-zA-Z\.])/,NR" \\1","1")}' <test.md >ln.md
```

a|b|c
--|--|--
foo
