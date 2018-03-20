import numpy as np
import pylab as plt
from astropy import units as u
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable


class MWPlot:
    """
    NAME: MWPlot
    PURPOSE:
    INPUT:
    OUTPUT:
    HISTORY:
        2018-Mar-17 - Written - Henry Leung (University of Toronto)
    """

    def __init__(self):
        self.fontsize = 25
        self.unit = u.lyr
        self.coord = None
        self.s = 1.0
        self.figsize = (20, 20)
        self.dpi = 200
        self.cmap = "viridis"
        self.imalpha = 0.85
        self.center = (0, 0) * u.lyr
        self.radius = 90750 * u.lyr
        self.tight_layout = True
        self.mw_annotation = True

        # Fixed value
        self.__pixels = 5600
        self.__resolution = 24.2 * u.lyr
        self.__fig = None

    def plot(self, *args, **kwargs):
        plt.plot(*args, **kwargs)

    @staticmethod
    def show(*args, **kwargs):
        plt.show(*args, **kwargs)

    def savefig(self, file='MWPlot.png'):
        if self.tight_layout is True:
            plt.tight_layout()

        # this is a pylab method
        self.__fig.savefig(file)

    def images_read(self):
        image_filename = 'MW_bg_annotate.png'
        if self.mw_annotation is False:
            image_filename = 'MW_bg_unannotate.png'

        try:
            img = plt.imread(image_filename)
        except FileNotFoundError:
            import mw_plot
            path = os.path.join(os.path.dirname(mw_plot.__path__[0]), 'mw_plot', image_filename)
            img = plt.imread(path)
        if self.coord == 'galactic':
            try:
                self.center[0] += -8. * u.kpc
            except TypeError:
                self.center[0] += -8.
            coord_english = 'Galactic Coordinates'
        elif self.coord == 'galactocentric':
            coord_english = 'Galactocentric Coordinates'
        else:
            raise ValueError("Unknown coordinates, can only be 'galactic' or 'galactocentric'")

        if not type(self.center) == u.quantity.Quantity and not type(self.radius) == u.quantity.Quantity:
            print(f"You did not specify units for center and radius, assuming the unit is {self.unit.long_names[0]}")
            if not type(self.center) == u.quantity.Quantity:
                self.center = self.center * self.unit
            if not type(self.radius) == u.quantity.Quantity:
                self.radius = self.radius * self.unit

        self.__resolution = self.__resolution.to(self.unit)
        self.center = self.center.to(self.unit)
        self.radius = self.radius.to(self.unit)

        # convert physical unit to pixel unit
        pixel_radius = int((self.radius / self.__resolution).value)
        pixel_center = list(map(int, (self.__pixels / 2 + self.center / self.__resolution).value))

        # get the pixel coordinates
        x_left_px = pixel_center[0] - pixel_radius
        x_right_px = pixel_center[0] + pixel_radius
        y_top_px = self.__pixels - pixel_center[1] - pixel_radius
        y_bottom_px = self.__pixels - pixel_center[1] + pixel_radius

        # decide whether it needs to fill black pixels because the range outside the pre-compiled images
        if np.all(np.array([x_left_px, self.__pixels - x_right_px, y_top_px, self.__pixels - y_bottom_px]) >= 0):
            img = img[y_top_px:y_bottom_px, x_left_px:x_right_px]
        else:
            # create a black image first with 3 channel with the same data type
            black_img = np.zeros((pixel_radius * 2, pixel_radius * 2, 3), dtype=img.dtype)

            # assign them to temp value
            # just in case the area is outside the images, will fill black pixel
            temp_x_left_px = max(x_left_px, 0)
            temp_x_right_px = min(x_right_px, self.__pixels)
            temp_y_top_px = max(y_top_px, 0)
            temp_y_bottom_px = min(y_bottom_px, self.__pixels)

            left_exceed_px = abs(min(x_left_px, 0))
            top_exceed_px = abs(min(y_top_px, 0))
            # Extract available area from pre-compiled first
            img = img[temp_y_top_px:temp_y_bottom_px, temp_x_left_px:temp_x_right_px]

            # fill the black image with the background image
            black_img[top_exceed_px:top_exceed_px + img.shape[0], left_exceed_px:left_exceed_px + img.shape[1], :] = img

            # Set the images as the filled black-background image
            img = np.array(black_img)

        ext = [(self.center[0] - self.radius).value, (self.center[0] + self.radius).value,
               (self.center[1] - self.radius).value, (self.center[1] + self.radius).value]

        return img, coord_english, ext

    def mw_plot(self, x, y, c, title=None):
        """
        NAME: mw_plot
        PURPOSE:
        INPUT:
        OUTPUT:
        HISTORY:
            2018-Mar-17 - Written - Henry Leung (University of Toronto)
        """
        cbar_flag = False

        unit_english = self.unit.long_names[0]

        if not type(x) == u.quantity.Quantity or not type(y) == u.quantity.Quantity:
            raise TypeError("Both x and y must carry astropy's unit")
        else:
            x = x.to(self.unit)
            y = y.to(self.unit)

        # Deal with coordinates issue, find out coordinates to the images area
        # extract a correct area of the image according to the center and radius provided
        img, coord_english, ext = self.images_read()

        # decide whether we need colorbar or not
        if isinstance(c, list):
            color = c[0]
            cbar_label = c[1]
            cbar_flag = True
        else:
            color = c

        self.__fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        plt.title(title, fontsize=self.fontsize)
        plt.xlabel(f'{coord_english} ({unit_english})', fontsize=self.fontsize)
        plt.ylabel(f'{coord_english} ({unit_english})', fontsize=self.fontsize)
        aspect = img.shape[0] / float(img.shape[1]) * ((ext[1] - ext[0]) / (ext[3] - ext[2]))
        ax = plt.gca()
        ax.set_aspect(aspect)
        ax.set_facecolor('k')  # have a black color background for image with <1.0 alpha
        plt.scatter(x, y, zorder=1, s=self.s, c=color, cmap=plt.get_cmap(self.cmap))
        ax.imshow(img, zorder=0, extent=ext, alpha=self.imalpha)

        if cbar_flag is True:
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cbar = plt.colorbar(cax=cax)
            cbar.ax.tick_params(labelsize=self.fontsize)
            cbar.set_label(f"{cbar_label}", size=self.fontsize)

        ax.tick_params(labelsize=self.fontsize)