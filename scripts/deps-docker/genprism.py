#!/usr/bin/env python3

# author: @chinponya


import argparse
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qsl


def read_json(path):
    return json.loads(path.read_text())


def get_prism_version(prism_path):
    package_json_path = prism_path / "package.json"
    package_json = read_json(package_json_path)
    return package_json["version"]


def get_prism_components(prism_path):
    components_json_path = prism_path / "components.json"
    components_json = read_json(components_json_path)
    return components_json


def parse_prism_configuration(url_str):
    url = urlparse(url_str)
    # prism.com uses a non-standard query string-like encoding
    query = {k: v.split(" ") for k, v in parse_qsl(url.fragment)}
    return query


def paths_of_component(prism_path, kind, components, name, minified):
    component = components[kind][name]
    meta = components[kind]["meta"]
    path_format = meta["path"]
    path_base = prism_path / path_format.replace("{id}", name)

    if isinstance(component, str):
        # 'core' component has a different shape, so we convert it to be consistent
        component = {"title": component}

    if meta.get("noCSS") or component.get("noCSS"):
        extensions = ["js"]
    elif kind == "themes":
        extensions = ["css"]
    else:
        extensions = ["js", "css"]

    if path_base.is_dir():
        result = {ext: path_base / f"{name}.{ext}" for ext in extensions}
    elif path_base.suffix:
        ext = path_base.suffix.replace(".", "")
        result = {ext: path_base}
    else:
        result = {ext: path_base.with_suffix(f".{ext}") for ext in extensions}

    if minified:
        result = {
            ext: path.with_suffix(".min" + path.suffix) for ext, path in result.items()
        }

    return result


def read_component_contents(kv_paths):
    return {k: path.read_text() for k, path in kv_paths.items()}


def get_language_dependencies(components, name):
    dependencies = components["languages"][name].get("require")

    if isinstance(dependencies, list):
        return dependencies
    elif isinstance(dependencies, str):
        return [dependencies]
    else:
        return []


def make_header(prism_path, url):
    version = get_prism_version(prism_path)
    header = f"/* PrismJS {version}\n{url} */"
    return {"js": header, "css": header}


def make_core(prism_path, components, minified):
    kv_paths = paths_of_component(prism_path, "core", components, "core", minified)
    return read_component_contents(kv_paths)


def make_theme(prism_path, components, name, minified):
    kv_paths = paths_of_component(prism_path, "themes", components, name, minified)
    return read_component_contents(kv_paths)


def make_language(prism_path, components, name, minified):
    kv_paths = paths_of_component(prism_path, "languages", components, name, minified)
    return read_component_contents(kv_paths)


def make_languages(prism_path, components, names, minified):
    names_with_dependencies = sum(
        ([*get_language_dependencies(components, name), name] for name in names), []
    )

    seen = set()
    names_with_dependencies = [
        x for x in names_with_dependencies if not (x in seen or seen.add(x))
    ]

    kv_code = [
        make_language(prism_path, components, name, minified)
        for name in names_with_dependencies
    ]

    return kv_code


def make_plugin(prism_path, components, name, minified):
    kv_paths = paths_of_component(prism_path, "plugins", components, name, minified)
    return read_component_contents(kv_paths)


def make_plugins(prism_path, components, names, minified):
    kv_code = [make_plugin(prism_path, components, name, minified) for name in names]
    return kv_code


def make_code(prism_path, url, minified):
    components = get_prism_components(prism_path)
    configuration = parse_prism_configuration(url)
    theme_name = configuration["themes"][0]
    code = [
        make_header(prism_path, url),
        make_core(prism_path, components, minified),
        make_theme(prism_path, components, theme_name, minified),
    ]

    if configuration.get("languages"):
        code.extend(
            make_languages(prism_path, components, configuration["languages"], minified)
        )

    if configuration.get("plugins"):
        code.extend(
            make_plugins(prism_path, components, configuration["plugins"], minified)
        )

    return code


def join_code(kv_code):
    result = {"js": "", "css": ""}

    for row in kv_code:
        for key, code in row.items():
            result[key] += code
            result[key] += "\n"

    return result


def write_code(kv_code, js_out, css_out):
    code = join_code(kv_code)

    with js_out.open("w") as f:
        f.write(code["js"])
        print(f"written {js_out}")

    with css_out.open("w") as f:
        f.write(code["css"])
        print(f"written {css_out}")


def parse_args():
    # fmt: off
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="configured prism download url")
    parser.add_argument("--dir", type=Path, default=Path("."), help="prism repo directory")
    parser.add_argument("--minify", default=True, action=argparse.BooleanOptionalAction, help="use minified files",)
    parser.add_argument("--js-out", type=Path, default=Path("prism.js"), help="JS output file path")
    parser.add_argument("--css-out", type=Path, default=Path("prism.css"), help="CSS output file path")
    # fmt: on
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    code = make_code(args.dir, args.url, args.minify)
    write_code(code, args.js_out, args.css_out)


if __name__ == "__main__":
    main()
