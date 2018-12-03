.. vim: set fileencoding=UTF-8 :
.. vim: set tw=80 :


Provider
--------

A `Provider` is the equivalent to a `Consumer` only that it transforms the
request handler's resulting model into a serialization requested from the
client. The client is then able to request a certain serialization using the
`Accept` header in her request.

Defining providers for a request handler is done using the `provides` decorator
on the class definition::

    @s.provides(s.MediaType.ApplicationJson)
    class MyHandler(s.RequestHandler):
        pass


Create custom provider
^^^^^^^^^^^^^^^^^^^^^^

A provider can be created equivalently to a consumer::

    class JsonProvider(ConsumerBase):

        CONTENT_TYPE = ContentType(MediaType.ApplicationJson)

        def provide(self, model, handler):
            try:
                model.validate()
                handler.write(model.to_primitive())
            except ModelValidationError as e:
                # for schematics 1.1.1, use e.messages instead
                raise HTTPError(500, reason=json.dumps(e.to_primitive()))

        def error(self, status_code, message, handler):
            handler.finish(message)


For `Producers` the same remarks about the content type hold as for the
`Consumers`.
