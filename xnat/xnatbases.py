from xnatcore import caching, XNATObject, XNATListing


class ProjectData(XNATObject):
    @property
    def fulluri(self):
        return '{}/projects/{}'.format(self.xnat.fulluri, self.id)

    @property
    @caching
    def subjects(self):
        return XNATListing(self.uri + '/subjects', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:subjectData')

    @property
    @caching
    def experiments(self):
        return XNATListing(self.uri + '/experiments', xnat=self.xnat, secondary_lookup_field='label')


class SubjectData(XNATObject):
    @property
    def fulluri(self):
        return '{}/projects/{}/subjects/{}'.format(self.xnat.fulluri, self.project, self.id)

    @property
    @caching
    def experiments(self):
        # HACK because self.uri + '/subjects' does not work
        uri = '{}/experiments'.format(self.fulluri, self.id)
        return XNATListing(uri, xnat=self.xnat, secondary_lookup_field='label')


class ImageSessionData(XNATObject):
    @property
    @caching
    def scans(self):
        return XNATListing(self.uri + '/scans', xnat=self.xnat, secondary_lookup_field='series_description')

    @property
    @caching
    def assessors(self):
        return XNATListing(self.uri + '/assessors', xnat=self.xnat, secondary_lookup_field='label')

    @property
    @caching
    def reconstructions(self):
        return XNATListing(self.uri + '/reconstructions', xnat=self.xnat, secondary_lookup_field='label')

    def add_assessor(self, label, type_='xnat:mrAssessorData'):
        uri = '{}/assessors/{label}?xsiType={type}&label={label}&req_format=qs'.format(self.uri,
                                                                                       type=type_,
                                                                                       label=label)
        self.xnat.put(uri, expected_code=(200, 201))
        self.clearcache()  # The resources changed, so we have to clear the cache

    def download(self, path):
        self.xnat.download_zip(self.uri + '/scans/ALL/files', path)


class DerivedData(XNATObject):
    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resourceData')

    def add_resource(self, label, format=None):
        uri = '{}/resources/{}'.format(self.uri, label)
        self.xnat.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache

    def download(self, path):
        self.xnat.download_zip(self.uri + '/files', path)


class ImageScanData(XNATObject):
    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resourceData')

    def add_resource(self, label, format=None):
        uri = '{}/resources/{}'.format(self.uri, label)
        self.xnat.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache

    def download(self, path):
        self.xnat.download_zip(self.uri + '/files', path)


class AbstractResource(XNATObject):
    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    def download(self, path):
        self.xnat.download_zip(self.uri + '/files', path)

    def upload(self, localpath, remotepath):
        print('[INFO] Upload to resource {}, local {}, remote {}'.format(self.id, localpath, remotepath))
        uri = '{}/files/{}'.format(self.uri, remotepath)
        self.xnat.upload(uri, localpath)


class File(XNATObject):
    def __init__(self, uri, xnat, id_=None, datafields=None, name=None):
        super(File, self).__init__(uri, xnat, id_=id_, datafields=datafields)
        if name is not None:
            self._cache['name'] = name

    @property
    @caching
    def name(self):
        return self.data['name']

    @property
    def xsi_type(self):
        return 'xnat:fileData'  # FIXME: is this correct?

    def download(self, path):
        self.xnat.download(self.uri, path)
