# -*- coding: utf-8 -*-

########### GUI2Exe SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### GUI2Exe SVN repository information ###################

# Start the imports

import os
import sys
import wx
import textwrap
import wx.lib.buttons as buttons

# For the nice throbber
import wx.animate

from Widgets import BaseListCtrl
from Utilities import opj, shortNow

if wx.Platform != "__WXMAC__":
    import extern.flatmenu as FM

# Get the I18N things
_ = wx.GetTranslation


class MessageWindow(wx.Panel):
    """
    A class which will show a list control at the bottom of our application.
    It is used to log messages coming from GUI2Exe.
    """

    def __init__(self, parent):
        """
        Default class constructor.

        
        **Parameters:**

        * parent: the widget parent.
        """

        wx.Panel.__init__(self, parent)
        self.MainFrame = wx.GetTopLevelParent(self)        

        # Add the fancy list at the bottom
        self.list = BaseListCtrl(self, columnNames=[_("Time        "), _("Compiler Messages")],
                                 name="messages")

        # Create 3 themed bitmap buttons
        dryBmp = self.MainFrame.CreateBitmap("dry")
        compileBmp = self.MainFrame.CreateBitmap("compile")
        killBmp = self.MainFrame.CreateBitmap("kill")

        # This is a bit tailored over py2exe, but it's the only one I know
        self.dryrun = buttons.ThemedGenBitmapTextButton(self, -1, dryBmp, _("Dry Run"), size=(-1, 25))
        self.compile = buttons.ThemedGenBitmapTextButton(self, -1, compileBmp, _("Compile"), size=(-1, 25))
        self.kill = buttons.ThemedGenBitmapTextButton(self, -1, killBmp, _("Kill"), size=(-1, 25))
        # The animation control
        ani = wx.animate.Animation(os.path.normpath(self.MainFrame.installDir +"/images/throbber.gif"))
        self.throb = wx.animate.AnimationCtrl(self, -1, ani)
        self.throb.SetUseWindowBackgroundColour()

        # Store an id for the popup menu
        self.popupId = wx.NewId()

        # Fo the hard work on other methods
        self.SetProperties()        
        self.LayoutItems()
        self.BindEvents()


    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets few properties for the list control. """

        font = self.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        
        # Set a bigger for for the compile and kill buttons
        self.compile.SetFont(font)
        self.kill.SetFont(font)
        self.kill.Enable(False)
        

    def LayoutItems(self):
        """ Layout the widgets with sizers. """

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # We have the main list filling all the space with a small reserved
        # zone on the right for the buttons
        buttonSizer.Add(self.dryrun, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT, 5)
        buttonSizer.Add(self.compile, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT, 5)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.throb, 0, wx.ALIGN_CENTER)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.kill, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT, 5)

        buttonSizer.Show(self.throb, False)
        buttonSizer.Layout()

        # Add everything to the main sizer        
        mainSizer.Add(self.list, 1, wx.EXPAND)
        mainSizer.Add(buttonSizer, 0, wx.EXPAND)
        self.SetSizer(mainSizer)
        mainSizer.Layout()

        # Keep a reference to the buttonSizer
        self.buttonSizer = buttonSizer

        
    def BindEvents(self):
        """ Bind the events for the list control. """

        self.Bind(wx.EVT_BUTTON, self.OnDryRun, self.dryrun)
        self.Bind(wx.EVT_BUTTON, self.OnCompile, self.compile)
        self.Bind(wx.EVT_BUTTON, self.OnKill, self.kill)
        self.Bind(wx.EVT_MENU, self.OnHistoryClear, id=self.popupId)
        self.list.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnRightClick)
        self.list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)

        if wx.Platform != "__WXMAC__":
            # Create a FlatMenu style popup and bind the events
            self.Bind(FM.EVT_FLAT_MENU_SELECTED, self.OnHistoryClear, id=self.popupId)


    # ============== #
    # Event handlers #
    # ============== #
    
    def OnDryRun(self, event):
        """ Handles the wx.EVT_BUTTON event for the dry run button. """
        
        # Delegate the action to the main frame
        self.MainFrame.RunCompile(view=False, run=False)


    def OnCompile(self, event):
        """ Handles the wx.EVT_BUTTON event for the compile button. """

        # Delegate the action to the main frame
        self.MainFrame.RunCompile(view=False, run=True)


    def OnKill(self, event):
        """ Handles the wx.EVT_BUTTON event for the kill button. """

        # Delegate the action to the main frame
        self.MainFrame.KillCompile()

        # Hide the throb
        self.ShowThrobber(False)
                          

    def OnRightClick(self, event):
        """
        Handles the wx.EVT_LIST_COL_RIGHT_CLICK/wx.EVT_LIST_ITEM_RIGHT_CLICK
        event for the list control.
        """

        flat, style = wx.GetApp().GetPreferences("Use_Flat_Menu", default=[0, (1, "Dark")])

        menu = (flat and [FM.FlatMenu()] or [wx.Menu()])[0]
        MenuItem = (flat and [FM.FlatMenuItem] or [wx.MenuItem])[0]

        # This pops up the "clear all" message
        item = MenuItem(menu, self.popupId, _("Clear History"))
        bmp = self.MainFrame.CreateBitmap("history_clear")
        item.SetBitmap(bmp)
        menu.AppendItem(item)        

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        if flat:
            menu.Popup(wx.GetMousePosition(), self)
        else:
            self.list.PopupMenu(menu)
            menu.Destroy()


    def OnHistoryClear(self, event):
        """ Handles the wx.EVT_MENU event for the list control. """

        # Freeze everything... It helps with flicker
        self.list.Freeze()
        # Delete all the items, the user cleared all
        self.list.DeleteAllItems()
        # Time to warm up
        self.list.Thaw()


    # ================= #
    # Auxiliary methods #
    # ================= #


    def ShowThrobber(self, show):
        """
        Shows/hides the throbber.

        
        **Parameters:**

        * show: whether to show or hide the throbber.
        """
        
        # Show/hide the throb
        self.buttonSizer.Show(self.throb, show)
        self.buttonSizer.Layout()
        # Refresh ourselves
        self.Refresh()
        if show:
            self.throb.Play()
        else:
            self.throb.Stop()


    def GetMaxWidth(self):
        """
        Returns the maximum number of characters that can fit in the message
        column.
        """

        # Use a wx.ClientDC to measure the maximum number of
        # characters we can fill for every list control row
        width = self.list.GetColumnWidth(2)
        font = self.list.GetFont()
        dc = wx.ClientDC(self.list)
        dc.SetFont(font)
        textWidth = dc.GetCharWidth()

        return int(width/float(textWidth))


    def InsertError(self, currentTime):
        """
        Insert some fancy line when an error happens.

        
        **Parameters:**

        * currentTime: the actual formatted time.
        """

        indx = self.list.InsertImageStringItem(sys.maxint, "", 2)
        self.list.SetStringItem(indx, 1, currentTime)
        self.list.SetStringItem(indx, 2, _("Error Message"))
        self.list.SetItemBackgroundColour(indx, wx.NamedColour("yellow"))
        font = self.list.GetFont()
        font.SetWeight(wx.BOLD)
        self.list.SetItemFont(indx, font)

        return indx        
    
    
    def SendMessage(self, kind, message, copy=False):
        """
        Prints an user-friendly message on the list control.

        
        **Parameters:**

        * kind: the message kind (error, warning, message);
        * message: the actual message to display in the list control;
        * copy: whether to save a reference to this message or not.
        """

        # Get the current time slightly dirrently formatted
        currentTime = shortNow()

        # Delete the "." at the end of the message (if any)
        message = message.strip()
        if message.endswith("."):
            message = message[:-1]
            
        # Wrap the message... error messages are often too long
        # to be seen in the list control
        width = self.GetMaxWidth()
        if kind == 2:  # is an error
            # Insert the correct icon (message, error, etc...) in the first column
            indx = self.InsertError(currentTime)
            messages = message.splitlines()
            message = []
            for msg in messages:
                message.extend(textwrap.wrap(msg, width))
        elif kind == 1 and "\n" in message:
            messages = message.splitlines()
            message = []
            for msg in messages:
                message.extend(textwrap.wrap(msg.strip(), width))
        else:
            message = [message]

        for msg in message:
            try:
                # Insert the correct icon (message, error, etc...) in the first column
                indx = self.list.InsertImageStringItem(sys.maxint, "", kind)
                # Insert the current time and the message
                self.list.SetStringItem(indx, 1, currentTime)
                self.list.SetStringItem(indx, 2, msg.encode())
            except UnicodeDecodeError:
                # Why does this happen here?!?
                continue
                
        # Ensure the last item is visible
        self.list.EnsureVisible(indx)
        if wx.Platform == "__WXGTK__":
            self.list.Refresh()
        if copy:
            # Save the last message
            self.list.lastMessage = [kind, msg]


    def CopyLastMessage(self):
        """ Re-sends the previous message to the log window (for long processes). """

        if not hasattr(self.list, "lastMessage"):
            return
        
        # Get the current time slightly dirrently formatted
        currentTime = shortNow()
        
        # Insert the correct icon (message, error, etc...) in the first column
        kind, msg = self.list.lastMessage
        indx = self.list.InsertImageStringItem(sys.maxint, "", kind)
        # Insert the current time and the message
        self.list.SetStringItem(indx, 1, currentTime)
        self.list.SetStringItem(indx, 2, msg)

        # Ensure the last item is visible
        self.list.EnsureVisible(indx)
        
        if wx.Platform == "__WXGTK__":
            self.list.Refresh()
            

    def EnableButtons(self, enable):
        """
        Enables/disables the run buttons depending on the external
        process status.

        
        **Parameters:**

        * enable: whether to enable or disable the buttons.
        """

        # dry run and compile buttons are enabled when the kill button is
        # not, and vice-versa
        self.dryrun.Enable(enable)
        self.compile.Enable(enable)
        self.kill.Enable(not enable)
        

    def EnableDryRun(self, book):
        """
        Enables/Disables the dry-run button depending on the selected compiler
        (dry-run is available only for py2exe).

        
        **Parameters:**

        * book: the L[LabelBook] associated to our project.        
        """

        # We enable the dry run option only if the selected compiler
        # is py2exe
        pageNum = book.GetSelection()
        self.dryrun.Enable(pageNum == 0)


    def NoPagesLeft(self, enable):
        """
        Enables/disables all the buttons depending on the number of projects opened.

        
        **Parameters:**

        * enable: whether to enable or disable the buttons.
        """

        self.dryrun.Enable(enable)
        self.compile.Enable(enable)
        self.kill.Enable(enable)

        