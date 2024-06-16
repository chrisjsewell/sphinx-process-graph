from sphinx.application import Sphinx

app = Sphinx("tester", None, "tester/build", "tester", "html")

print(list(app.events.listeners))

event_name = "env-check-consistency"
print(event_name, len(app.events.listeners[event_name]))
for ev in app.events.listeners[event_name]:
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


transforms = sorted(
    (t.default_priority, i, t) for i, t in enumerate(app.registry.get_post_transforms())
)
for priority, _, transform in transforms:
    path = f"{transform.__module__}.{transform.__qualname__}"
    doc = transform.__doc__
    builders = list(getattr(transform, "builders", []))
    formats = list(getattr(transform, "formats", []))
    print(
        f'"{path}" = {{priority={priority}, builders={builders}, formats={formats}, doc = """'
    )
    print(doc)
    print('"""}')


def find_overriding_class(cls, method_name):
    for subclass in cls.__mro__:
        if method_name in subclass.__dict__:
            return subclass
    return None


for name, builder in sorted(app.registry.builders.items()):
    print(f"{name} = {builder}")
    print(f"    write: {find_overriding_class(builder, 'write')}")
    print(f"    finish: {find_overriding_class(builder, 'finish')}")
