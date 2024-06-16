from sphinx.application import Sphinx

app = Sphinx("tester", None, "tester/build", "tester", "html")

print(list(app.events.listeners))

print(len(app.events.listeners["doctree-read"]))

for ev in app.events.listeners["doctree-read"]:
    if hasattr(ev.handler, "__self__"):
        base = ev.handler.__self__.__module__
        qual = ev.handler.__self__.__class__.__name__ + "." + ev.handler.__name__
    else:
        base = ev.handler.__module__
        qual = ev.handler.__qualname__
    path = f"{base}.{qual}"
    doc = ev.handler.__doc__
    print(f'"{path}" = {{priority = {ev.priority}, doc = """')
    print(doc)
    print('"""}')


transforms = sorted(
    (t.default_priority, i, t)
    for i, t in enumerate(
        app.registry.get_publisher(app, "rst").reader.get_transforms()
    )
)
for priority, _, transform in transforms:
    path = f"{transform.__module__}.{transform.__qualname__}"
    doc = transform.__doc__
    print(f'"{path}" = {{priority = {priority}, doc = """')
    print(doc)
    print('"""}')
