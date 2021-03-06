from __future__ import unicode_literals

import json

from mopidy import models

import pytest

import responses

import mopidy_spotify
from mopidy_spotify import images


@pytest.fixture
def img_provider(provider):
    images._cache = {}
    return provider


@responses.activate
def test_get_artist_images(img_provider):
    uris = [
        'spotify:artist:4FCGgZrVQtcbDFEap3OAb2',
        'http://open.spotify.com/artist/0Nsz79ZcE8E4i3XZhCzZ1l',
    ]

    responses.add(
        responses.GET, 'https://api.spotify.com/v1/artists/',
        body=json.dumps({
            'artists': [
                {
                    'id': '4FCGgZrVQtcbDFEap3OAb2',
                    'images': [
                        {
                            'height': 640,
                            'url': 'img://1/a',
                            'width': 640,
                        },
                        {
                            'height': 300,
                            'url': 'img://1/b',
                            'width': 300,
                        },
                    ]
                },
                {
                    'id': '0Nsz79ZcE8E4i3XZhCzZ1l',
                    'images': [
                        {
                            'height': 64,
                            'url': 'img://2/a',
                            'width': 64
                        }
                    ]
                }
            ]
        })
    )

    result = img_provider.get_images(uris)

    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.url ==
        'https://api.spotify.com/v1/artists/?ids='
        '4FCGgZrVQtcbDFEap3OAb2,0Nsz79ZcE8E4i3XZhCzZ1l')
    assert responses.calls[0].request.headers['User-Agent'].startswith(
        'Mopidy-Spotify/%s' % mopidy_spotify.__version__)

    assert len(result) == 2
    assert sorted(result.keys()) == sorted(uris)

    assert len(result[uris[0]]) == 2
    assert len(result[uris[1]]) == 1

    image1a = result[uris[0]][0]
    assert isinstance(image1a, models.Image)
    assert image1a.uri == 'img://1/a'
    assert image1a.height == 640
    assert image1a.width == 640

    image1b = result[uris[0]][1]
    assert isinstance(image1b, models.Image)
    assert image1b.uri == 'img://1/b'
    assert image1b.height == 300
    assert image1b.width == 300

    image2a = result[uris[1]][0]
    assert isinstance(image2a, models.Image)
    assert image2a.uri == 'img://2/a'
    assert image2a.height == 64
    assert image2a.width == 64


@responses.activate
def test_get_album_images(img_provider):
    uris = [
        'http://play.spotify.com/album/1utFPuvgBHXzLJdqhCDOkg',
    ]

    responses.add(
        responses.GET, 'https://api.spotify.com/v1/albums/',
        body=json.dumps({
            'albums': [
                {
                    'id': '1utFPuvgBHXzLJdqhCDOkg',
                    'images': [
                        {
                            'height': 640,
                            'url': 'img://1/a',
                            'width': 640,
                        }
                    ]
                }
            ]
        })
    )

    result = img_provider.get_images(uris)

    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.url ==
        'https://api.spotify.com/v1/albums/?ids=1utFPuvgBHXzLJdqhCDOkg')

    assert len(result) == 1
    assert sorted(result.keys()) == sorted(uris)
    assert len(result[uris[0]]) == 1

    image = result[uris[0]][0]
    assert isinstance(image, models.Image)
    assert image.uri == 'img://1/a'
    assert image.height == 640
    assert image.width == 640


@responses.activate
def test_get_track_images(img_provider):
    uris = [
        'spotify:track:41shEpOKyyadtG6lDclooa',
    ]

    responses.add(
        responses.GET, 'https://api.spotify.com/v1/tracks/',
        body=json.dumps({
            'tracks': [
                {
                    'id': '41shEpOKyyadtG6lDclooa',
                    'album': {
                        'uri': 'spotify:album:1utFPuvgBHXzLJdqhCDOkg',
                        'images': [
                            {
                                'height': 640,
                                'url': 'img://1/a',
                                'width': 640,
                            }
                        ]
                    }
                }
            ]
        })
    )

    result = img_provider.get_images(uris)

    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.url ==
        'https://api.spotify.com/v1/tracks/?ids=41shEpOKyyadtG6lDclooa')

    assert len(result) == 1
    assert sorted(result.keys()) == sorted(uris)
    assert len(result[uris[0]]) == 1

    image = result[uris[0]][0]
    assert isinstance(image, models.Image)
    assert image.uri == 'img://1/a'
    assert image.height == 640
    assert image.width == 640


@responses.activate
def test_results_are_cached(img_provider):
    uris = [
        'spotify:track:41shEpOKyyadtG6lDclooa',
    ]

    responses.add(
        responses.GET, 'https://api.spotify.com/v1/tracks/',
        body=json.dumps({
            'tracks': [
                {
                    'id': '41shEpOKyyadtG6lDclooa',
                    'album': {
                        'uri': 'spotify:album:1utFPuvgBHXzLJdqhCDOkg',
                        'images': [
                            {
                                'height': 640,
                                'url': 'img://1/a',
                                'width': 640,
                            }
                        ]
                    }
                }
            ]
        })
    )

    result1 = img_provider.get_images(uris)
    result2 = img_provider.get_images(uris)

    assert len(responses.calls) == 1
    assert result1 == result2


@responses.activate
def test_max_50_ids_per_request(img_provider):
    uris = ['spotify:track:%d' % i for i in range(51)]

    responses.add(responses.GET, '', body=json.dumps({}))

    img_provider.get_images(uris)

    assert len(responses.calls) == 2

    request_url_1 = responses.calls[0].request.url
    assert request_url_1.endswith(','.join(str(i) for i in range(50)))

    request_url_2 = responses.calls[1].request.url
    assert request_url_2.endswith('ids=50')


def test_invalid_uri_fails(img_provider):
    with pytest.raises(ValueError) as exc:
        img_provider.get_images(['foo:bar'])

    assert str(exc.value) == "Could not parse u'foo:bar' as a Spotify URI"


def test_no_uris_gives_no_results(img_provider):
    result = img_provider.get_images([])

    assert result == {}


@responses.activate
def test_service_returns_invalid_json(img_provider, caplog):
    responses.add(
        responses.GET, 'https://api.spotify.com/v1/tracks/', body='abc')

    result = img_provider.get_images(['spotify:track:41shEpOKyyadtG6lDclooa'])

    assert result == {}
    assert "JSON decoding failed for" in caplog.text()


@responses.activate
def test_service_returns_empty_result(img_provider):
    responses.add(
        responses.GET, 'https://api.spotify.com/v1/tracks/',
        body=json.dumps({'tracks': [{}]}))

    result = img_provider.get_images(['spotify:track:41shEpOKyyadtG6lDclooa'])

    assert result == {}
