# hi
this showcases my worst idea yet; *extending markdown with inline javascript*

due to obvious reasons it's disabled by default, and can be enabled with `-emp`

the examples are by no means correct, they're as much of a joke as this feature itself


### sub-header
nothing special about this one


## except/
this one becomes a hyperlink to ./except/ thanks to
* the `copyparty_pre` plugin at the end of this file
* which is invoked as a markdown filter every time the document is modified
* which looks for headers ending with a `/` and erwrites all headers below that

it is a passthrough to the markdown extension api, see https://marked.js.org/using_pro


### these/
and this one becomes ./except/these/


#### ones.md
finally ./except/these/ones.md


### also-this.md
whic hshoud be ./except/also-this.md




# ok
now for another extension type, `copyparty_post` which is called to manipulate the generated dom instead

the values in the `ex:` columns are linkified to `example.com/$value`

| ex:foo       | bar      | ex:baz |
| ------------ | -------- | ------ |
| asdf         | nice     | fgsfds |
| more one row | hi hello | aaa    |

the difference is that with `copyparty_pre` you'll probably break various copyparty features but if you use `copyparty_post` then future copyparty versions will probably break you




# heres the plugins
if there is anything below ths line in the preview then the plugin feature is disabled (good)




```copyparty_pre
ctor() {
    md_plug['h'] = {
        on: false,
        lv: -1,
        path: []
    }
},
walkTokens(token) {
    if (token.type == 'heading') {
        var h = md_plug['h'],
            is_dir = token.text.endsWith('/');
        
        if (h.lv >= token.depth) {
            h.on = false;
        }
        if (!h.on && is_dir) {
            h.on = true;
            h.lv = token.depth;
            h.path = [token.text];
        }
        else if (h.on && h.lv < token.depth) {
            h.path = h.path.slice(0, token.depth - h.lv);
            h.path.push(token.text);
        }
        if (!h.on)
            return false;

        var path = h.path.join('');
        var emoji = is_dir ? '📂' : '📜';
        token.tokens[0].text = '<a href="' + path + '">' + emoji + ' ' + path + '</a>';
    }
    if (token.type == 'paragraph') {
        //console.log(JSON.parse(JSON.stringify(token.tokens)));
        for (var a = 0; a < token.tokens.length; a++) {
            var t = token.tokens[a];
            if (t.type == 'text' || t.type == 'strong' || t.type == 'em') {
                var ret = '', text = t.text;
                for (var b = 0; b < text.length; b++)
                    ret += (Math.random() > 0.5) ? text[b] : text[b].toUpperCase();
                
                t.text = ret;
            }
        }
    }
    return true;
}
```



```copyparty_post
render(dom) {
    var ths = dom.querySelectorAll('th');
    for (var a = 0; a < ths.length; a++) {
        var th = ths[a];
        if (th.textContent.indexOf('ex:') === 0) {
            th.textContent = th.textContent.slice(3);
            var nrow = 0;
            while ((th = th.previousSibling) != null)
                nrow++;
            
            var trs = ths[a].parentNode.parentNode.parentNode.querySelectorAll('tr');
            for (var b = 1; b < trs.length; b++) {
                var td = trs[b].childNodes[nrow];
                td.innerHTML = '<a href="//example.com/' + td.innerHTML + '">' + td.innerHTML + '</a>';
            }
        }
    }
}
```
