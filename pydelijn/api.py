"""
Get realtime info on stop passages of De Lijn (api.delijn.be).

A module to get information about the next passages from a stop
of De Lijn, the public transportation company of Flanders (Belgium).

This code is released under the terms of the MIT license. See the LICENSE
file for more details.
"""
from datetime import datetime
import pytz

from .common import BASE_URL, LOGGER


class Passages():
    """A class to get passage information."""

    def __init__(self,
                 loop,
                 stopid,
                 maxpassages,
                 subscriptionkey,
                 session=None):
        """Initialize the class."""
        self.loop = loop
        self.session = session
        self.stopid = str(stopid)
        self.maxpassages = maxpassages
        self.subscriptionkey = subscriptionkey
        self._passages = []

    async def get_passages(self):
        """Get passages info from stopid."""
        from .common import CommonFunctions
        selfcreatedsession = False
        if self.session is None:
            selfcreatedsession = True
        entitynum = self.stopid[:1]
        common = CommonFunctions(self.loop, self.session, self.subscriptionkey)
        passages = []
        tzone = pytz.timezone('Europe/Brussels')

        endpointcolours = '{}kleuren/'.format(BASE_URL)
        colourshex = {}
        resultcolours = await common.api_call(endpointcolours)
        if resultcolours is not None:
            for colours in resultcolours['kleuren']:
                colourshex.update(
                    {str(colours.get('code')): colours.get('hex')}
                )

        stopname = str(self.stopid)
        endpointstop = '{}haltes/{}/{}'.format(BASE_URL,
                                               str(entitynum),
                                               str(self.stopid))
        resultstop = await common.api_call(endpointstop)
        if resultstop is not None:
            stopname = "{}, {}".format(
                str(resultstop.get('omschrijving')),
                str(resultstop.get('omschrijvingGemeente')))

        endpointrealtime = '{}haltes/{}/{}/real-time'.format(BASE_URL,
                                                             str(entitynum),
                                                             str(self.stopid))
        resultrealtime = await common.api_call(endpointrealtime)
        if resultrealtime is not None:
            for stoppassages in resultrealtime['halteDoorkomsten'] or []:
                try:
                    for index, passage in zip(range(self.maxpassages),
                                              stoppassages['doorkomsten']):
                        ent_num = passage.get('entiteitnummer')
                        linenumber = passage.get('lijnnummer')
                        direction = passage.get('richting')
                        final_destination = passage.get('bestemming')
                        due_at_sch = passage.get('dienstregelingTijdstip')
                        due_at_rt = passage.get('real-timeTijdstip')
                        due_in_min = None

                        if due_at_rt is not None:
                            dt_rt_local = tzone.localize(
                                datetime.strptime(
                                    due_at_rt,
                                    "%Y-%m-%dT%H:%M:%S"),
                                is_dst=None)
                            dt_now_local = tzone.localize(
                                datetime.now(),
                                is_dst=None)
                            diff = dt_rt_local - dt_now_local
                            due_in_min = int(diff.total_seconds() / 60)
                        elif due_at_sch is not None:
                            dt_rt_local = tzone.localize(
                                datetime.strptime(
                                    due_at_sch,
                                    "%Y-%m-%dT%H:%M:%S"),
                                is_dst=None)
                            dt_now_local = tzone.localize(
                                datetime.now(),
                                is_dst=None)
                            diff = dt_rt_local - dt_now_local
                            due_in_min = int(diff.total_seconds() / 60)

                        endpointlinepublic = '{}lijnen/{}/{}'.format(
                            BASE_URL,
                            str(ent_num),
                            str(linenumber))
                        resultlinepublic = await common.api_call(
                            endpointlinepublic)
                        if resultlinepublic is not None:
                            linenumberpublic = resultlinepublic.get(
                                'lijnnummerPubliek')
                            linedesc = resultlinepublic.get(
                                'omschrijving')
                            linetransporttype = resultlinepublic.get(
                                'vervoertype')

                            endpointlinecolours = ("{}lijnen/{}/"
                                                   "{}/lijnkleuren".format(
                                                       BASE_URL,
                                                       str(ent_num),
                                                       str(linenumber)))
                            resultlinecolours = await common.api_call(
                                endpointlinecolours)
                            if resultlinecolours is not None:
                                linenumcolfront = resultlinecolours.get(
                                    'voorgrond').get('code')
                                linenumcolfronthex = colourshex.get(
                                    str(linenumcolfront))
                                linenumcolback = resultlinecolours.get(
                                    'achtergrond').get('code')
                                linenumcolbackhex = colourshex.get(
                                    str(linenumcolback))
                                linenumcolfrontborder = resultlinecolours.get(
                                    'voorgrondRand').get('code')
                                linenumcolfrontborderhex = colourshex.get(
                                    str(linenumcolfrontborder))
                                linenumcolbackborder = resultlinecolours.get(
                                    'achtergrondRand').get('code')
                                linenumcolbackborderhex = colourshex.get(
                                    str(linenumcolbackborder))

                                passages.append({
                                    'passage':
                                        index,
                                    'stopname':
                                        stopname,
                                    'line_number':
                                        linenumber,
                                    'direction':
                                        direction,
                                    'final_destination':
                                        final_destination,
                                    'due_at_sch':
                                        due_at_sch,
                                    'due_at_rt':
                                        due_at_rt,
                                    'due_in_min':
                                        due_in_min,
                                    'line_number_public':
                                        linenumberpublic,
                                    'line_desc':
                                        linedesc,
                                    'line_transport_type':
                                        linetransporttype,
                                    'line_number_colourFront':
                                        linenumcolfront,
                                    'line_number_colourFrontHex':
                                        linenumcolfronthex,
                                    'line_number_colourBack':
                                        linenumcolback,
                                    'line_number_colourBackHex':
                                        linenumcolbackhex,
                                    'line_number_colourFrontBorder':
                                        linenumcolfrontborder,
                                    'line_number_colourFrontBorderHex':
                                        linenumcolfrontborderhex,
                                    'line_number_colourBackBorder':
                                        linenumcolbackborder,
                                    'line_number_colourBackBorderHex':
                                        linenumcolbackborderhex})
                except (TypeError, KeyError, IndexError) as error:
                    LOGGER.error('Error connecting to De Lijn api, %s', error)
        if selfcreatedsession is True:
            await common.close()
        self._passages = passages

    @property
    def passages(self):
        """Return the passages."""
        return self._passages
