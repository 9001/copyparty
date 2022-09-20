# builds win7-i386 exe on win10-ltsc-1809(17763.316)
# see docs/pyoxidizer.txt

def make_exe():
    dist = default_python_distribution(flavor="standalone_static", python_version="3.8")
    policy = dist.make_python_packaging_policy()
    policy.allow_files = True
    policy.allow_in_memory_shared_library_loading = True
    #policy.bytecode_optimize_level_zero = True
    #policy.include_distribution_sources = False  # error instantiating embedded Python interpreter: during initializing Python main: init_fs_encoding: failed to get the Python codec of the filesystem encoding
    policy.include_distribution_resources = False
    policy.include_non_distribution_sources = False
    policy.include_test = False
    python_config = dist.make_python_interpreter_config()
    #python_config.module_search_paths = ["$ORIGIN/lib"]

    python_config.run_module = "copyparty"
    exe = dist.to_python_executable(
        name="copyparty",
        config=python_config,
        packaging_policy=policy,
    )
    exe.windows_runtime_dlls_mode = "never"
    exe.windows_subsystem = "console"
    exe.add_python_resources(exe.read_package_root(
        path="sfx",
        packages=[
            "copyparty",
            "jinja2",
            "markupsafe",
            "pyftpdlib",
            "python-magic",
        ]
    ))
    return exe

def make_embedded_resources(exe):
    return exe.to_embedded_resources()

def make_install(exe):
    files = FileManifest()
    files.add_python_resource("copyparty", exe)
    return files

register_target("exe", make_exe)
register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
register_target("install", make_install, depends=["exe"], default=True)
resolve_targets()
